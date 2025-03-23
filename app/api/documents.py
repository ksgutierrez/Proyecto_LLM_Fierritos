# app/api/documents.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
import os
from typing import List, Optional
from app.db.session import get_db
from app.models.document import Document
from app.schemas.document import Document as DocumentSchema, DocumentCreate
from app.services.document_processor import DocumentProcessor
from app.services.llm_service import LLMService
from app.services.vector_store import VectorStore
from app.api.auth import get_current_user_id
from google.cloud import aiplatform

router = APIRouter()

@router.post("/upload", response_model=DocumentSchema)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Sube un documento para procesamiento RAG."""
    try:
        # Validar tipo de archivo
        valid_extensions = ['.pdf', '.docx', '.txt', '.md']
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in valid_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no soportado. Formatos válidos: {', '.join(valid_extensions)}"
            )
        
        # Procesar documento y generar resumen
        content, file_path, summary = await DocumentProcessor.process_document(file, current_user_id)
        
        # Guardar en base de datos
        document = Document(
            title=file.filename,
            content=content,
            file_path=file_path,
            summary=summary,
            owner_id=current_user_id
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        return document
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar el documento: {str(e)}"
        )

@router.get("/documents", response_model=List[DocumentSchema])
async def get_documents(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Obtiene todos los documentos del usuario actual."""
    documents = db.query(Document).filter(Document.owner_id == current_user_id).all()
    return documents

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """Elimina un documento del usuario actual."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    try:
        # Eliminar el archivo físico si existe
        if document.file_path and os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Eliminar embeddings del documento en ChromaDB
        vector_store = VectorStore()
        vector_store.delete_by_filter({
            "user_id": current_user_id,
            "source": os.path.basename(document.file_path)
        })
        
        # Eliminar de la base de datos
        db.delete(document)
        db.commit()
        
        return {"message": "Documento eliminado correctamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar el documento: {str(e)}"
        )

@router.post("/ask/{document_id}")
async def ask_question(
    document_id: int,
    question: str = Query(..., description="Pregunta sobre el documento"),
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Responde una pregunta sobre un documento utilizando RAG (Retrieval Augmented Generation).
    Recupera los chunks más relevantes del documento y utiliza Google Flash API para generar una respuesta.
    """
    # Verificar que el documento existe y pertenece al usuario
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == current_user_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    try:
        # Inicializar servicios
        llm_service = LLMService()
        vector_store = VectorStore()
        
        # Generar embedding para la pregunta
        # Configurar cliente de embeddings
        embedding_model = aiplatform.TextEmbeddingModel.from_pretrained("textembedding-gecko@latest")
        query_embedding_response = embedding_model.get_embeddings([question])
        query_embedding = query_embedding_response[0].values
        
        # Recuperar chunks relevantes del documento
        relevant_chunks = vector_store.similarity_search(
            query_embedding=query_embedding,
            k=3,  # Número de chunks a recuperar
            filter_dict={
                "user_id": current_user_id,
                "source": os.path.basename(document.file_path)
            }
        )
        
        if not relevant_chunks:
            # Si no hay chunks relevantes, usar el documento completo
            answer = await llm_service.answer_question(document.content[:4000], question)
            return {"answer": answer}
        
        # Generar respuesta con los chunks más relevantes
        answer = await llm_service.answer_question_with_sources(question, relevant_chunks)
        return {"answer": answer}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar la pregunta: {str(e)}"
        )

@router.post("/search")
async def search_across_documents(
    query: str = Query(..., description="Consulta de búsqueda"),
    limit: int = Query(5, description="Número máximo de resultados"),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    Busca en todos los documentos del usuario utilizando similitud semántica.
    Devuelve fragmentos relevantes de los documentos que coinciden con la consulta.
    """
    try:
        # Generar embedding para la consulta
        embedding_model = aiplatform.TextEmbeddingModel.from_pretrained("textembedding-gecko@latest")
        query_embedding_response = embedding_model.get_embeddings([query])
        query_embedding = query_embedding_response[0].values
        
        # Buscar en la base de datos vectorial
        vector_store = VectorStore()
        results = vector_store.similarity_search(
            query_embedding=query_embedding,
            k=limit,
            filter_dict={"user_id": current_user_id}
        )
        
        # Formatear resultados
        formatted_results = []
        for result in results:
            formatted_results.append({
                "text": result["text"],
                "score": result["score"],
                "document": result["metadata"]["source"],
                "page": result["metadata"].get("page", "N/A")
            })
        
        return {"results": formatted_results}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al realizar la búsqueda: {str(e)}"
        )