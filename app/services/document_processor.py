# app/services/document_processor.py
from .celery_config import celery_app
import os
from typing import Optional, Tuple, List, Dict, Any
from fastapi import UploadFile
import PyPDF2
import docx
import markdown
import numpy as np
from .llm_service import LLMService
from .vector_store import VectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from google.cloud import aiplatform
from google.oauth2 import service_account
import time

class DocumentProcessor:
    @staticmethod
    async def process_document(file: UploadFile, user_id: int) -> Tuple[str, str, Optional[str]]:
        """
        Procesa un documento subido por el usuario.
        
        Args:
            file: Archivo subido
            user_id: ID del usuario propietario
            
        Returns:
            Tuple con (contenido, ruta del archivo, resumen)
        """
        content = ""
        file_path = f"uploads/{user_id}/{file.filename}"
        os.makedirs(f"uploads/{user_id}", exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content_bytes = await file.read()
            buffer.write(content_bytes)
        
        if file.filename.endswith('.pdf'):
            content = DocumentProcessor._process_pdf(file_path)
        elif file.filename.endswith('.docx'):
            content = DocumentProcessor._process_docx(file_path)
        elif file.filename.endswith('.md'):
            content = DocumentProcessor._process_markdown(file_path)
        elif file.filename.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        # Generate summary using LLM
        try:
            llm_service = LLMService()
            # Use the first 2000 characters to generate a summary
            text_to_summarize = content[:2000]
            summary = await llm_service.generate_summary(text_to_summarize)
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            summary = "No summary available"
                
        # Inicia el procesamiento asíncrono para chunking y embeddings
        process_document_task.delay(file_path, content, user_id)
        return content, file_path, summary

    @staticmethod
    def _process_pdf(file_path: str) -> str:
        """Extrae texto de un archivo PDF."""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"[Page {page_num + 1}]\n{page_text}\n\n"
        return text

    @staticmethod
    def _process_docx(file_path: str) -> str:
        """Extrae texto de un archivo DOCX."""
        doc = docx.Document(file_path)
        return " ".join([paragraph.text for paragraph in doc.paragraphs])

    @staticmethod
    def _process_markdown(file_path: str) -> str:
        """Extrae texto de un archivo Markdown."""
        with open(file_path, 'r', encoding='utf-8') as file:
            return markdown.markdown(file.read())
            
    @staticmethod
    def chunk_text(text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Divide el texto en chunks para su procesamiento.
        
        Args:
            text: Texto a dividir
            metadata: Metadatos asociados al documento
            
        Returns:
            Lista de diccionarios con texto y metadatos
        """
        # Configurar splitter para chunks óptimos para RAG
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Dividir el texto en chunks
        chunks = text_splitter.split_text(text)
        
        # Crear lista de chunks con metadatos
        result = []
        for i, chunk_text in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata["chunk_id"] = i
            result.append({
                "text": chunk_text,
                "metadata": chunk_metadata
            })
        
        return result

@celery_app.task
def process_document_task(file_path: str, content: str, user_id: int):
    """
    Tarea Celery para procesar un documento en segundo plano.
    Divide el documento en chunks y genera embeddings.
    
    Args:
        file_path: Ruta al archivo
        content: Contenido textual del archivo
        user_id: ID del usuario propietario
    """
    try:
        print(f"Iniciando procesamiento de documento: {file_path}")
        file_name = os.path.basename(file_path)
        
        # Metadatos básicos
        metadata = {
            "source": file_name,
            "user_id": user_id,
            "path": file_path,
            "processed_at": time.time()
        }
        
        # Detectar si es un PDF para incluir información de páginas
        if file_path.endswith('.pdf'):
            # Procesar metadatos de página
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_texts = []
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        page_metadata = metadata.copy()
                        page_metadata["page"] = page_num + 1
                        page_chunks = DocumentProcessor.chunk_text(page_text, page_metadata)
                        for chunk in page_chunks:
                            process_chunk(chunk, user_id)
        else:
            # Documentos que no son PDF
            chunks = DocumentProcessor.chunk_text(content, metadata)
            for chunk in chunks:
                process_chunk(chunk, user_id)
                
        print(f"Procesamiento completado para documento: {file_path}")
        
    except Exception as e:
        print(f"Error procesando documento: {str(e)}")

def process_chunk(chunk: Dict[str, Any], user_id: int):
    """
    Procesa un chunk individual: genera embedding y lo almacena.
    
    Args:
        chunk: Diccionario con texto y metadatos
        user_id: ID del usuario propietario
    """
    try:
        # Inicializar store para embeddings
        vector_store = VectorStore()
        
        # Generar embedding para el chunk
        embedding = generate_embedding(chunk["text"])
        
        # Guardar en la base de datos vectorial
        vector_store.add_texts(
            texts=[chunk["text"]],
            embeddings=[embedding],
            metadatas=[chunk["metadata"]],
            ids=[f"{user_id}_{chunk['metadata']['source']}_{chunk['metadata'].get('chunk_id')}"]
        )
        
    except Exception as e:
        print(f"Error procesando chunk: {str(e)}")

def generate_embedding(text: str) -> List[float]:
    """
    Genera embeddings para un texto utilizando la API de Google.
    
    Args:
        text: Texto para generar embedding
        
    Returns:
        Vector de embedding
    """
    try:
        # Configurar credenciales
        if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            credentials = service_account.Credentials.from_service_account_file(
                os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            )
            client = aiplatform.TextEmbeddingModel(
                model_name="textembedding-gecko@latest",
                credentials=credentials
            )
        else:
            client = aiplatform.TextEmbeddingModel(
                model_name="textembedding-gecko@latest"
            )
        
        # Generar embedding
        embeddings = client.get_embeddings([text])
        
        # Obtener el resultado
        if embeddings and embeddings[0]:
            return embeddings[0].values
        else:
            # Fallback a un embedding aleatorio (solo para desarrollo)
            print("Warning: Fallback a embedding aleatorio")
            return list(np.random.randn(768))
            
    except Exception as e:
        print(f"Error generando embedding: {str(e)}")
        # Fallback a un embedding aleatorio (solo para desarrollo)
        return list(np.random.randn(768))