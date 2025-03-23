# app/services/vector_store.py
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from app.core.config import settings

class VectorStore:
    """
    Clase para gestionar la base de datos vectorial ChromaDB.
    Proporciona métodos para añadir y recuperar embeddings.
    """
    
    _instance = None
    
    def __new__(cls):
        """Implementación singleton para asegurar una sola instancia por proceso."""
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializa la conexión a ChromaDB."""
        if self._initialized:
            return
            
        # Crear directorio de persistencia
        os.makedirs("vector_db", exist_ok=True)
        
        # Inicializar cliente de ChromaDB
        self.client = chromadb.PersistentClient(
            path="vector_db",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Obtener o crear la colección
        self.collection = self.client.get_or_create_collection(
            name="documents",
            embedding_function=None,  # Usamos embeddings pre-calculados
            metadata={"hnsw:space": "cosine"}  # Usar distancia coseno
        )
        
        self._initialized = True
        print("ChromaDB inicializado correctamente")
    
    def add_texts(
        self, 
        texts: List[str], 
        embeddings: List[List[float]], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Añade textos y sus embeddings a la base de datos vectorial.
        
        Args:
            texts: Lista de textos
            embeddings: Lista de embeddings (vectores)
            metadatas: Lista de metadatos asociados a cada texto
            ids: Lista de identificadores únicos
            
        Returns:
            Lista de IDs asignados
        """
        try:
            # Si no se proporcionan IDs, usar hashes de los textos
            if not ids:
                import hashlib
                ids = [
                    hashlib.md5(f"{text}_{i}".encode()).hexdigest()
                    for i, text in enumerate(texts)
                ]
            
            # Añadir a ChromaDB
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            return ids
            
        except Exception as e:
            print(f"Error añadiendo textos a ChromaDB: {str(e)}")
            raise
    
    def similarity_search(
        self, 
        query_embedding: List[float], 
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca los documentos más similares a un embedding de consulta.
        
        Args:
            query_embedding: Vector de embedding de la consulta
            k: Número de resultados a devolver
            filter_dict: Filtro opcional para la búsqueda (ej: {"user_id": 123})
            
        Returns:
            Lista de documentos con sus metadatos y puntuaciones
        """
        try:
            # Realizar búsqueda
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=filter_dict
            )
            
            # Formatear resultados
            formatted_results = []
            if results and results.get('documents') and len(results['documents']) > 0:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]
                ids = results['ids'][0]
                
                for i in range(len(documents)):
                    formatted_results.append({
                        "id": ids[i],
                        "text": documents[i],
                        "metadata": metadatas[i],
                        "score": 1.0 - distances[i]  # Convertir distancia a similitud
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error en búsqueda de similitud: {str(e)}")
            return []
    
    def delete_by_filter(self, filter_dict: Dict[str, Any]) -> int:
        """
        Elimina documentos que coinciden con un filtro.
        
        Args:
            filter_dict: Filtro para seleccionar documentos a eliminar
            
        Returns:
            Número de documentos eliminados
        """
        try:
            # Obtener IDs que coinciden con el filtro
            matching = self.collection.get(where=filter_dict)
            if not matching or not matching['ids']:
                return 0
                
            # Eliminar por IDs
            self.collection.delete(ids=matching['ids'])
            return len(matching['ids'])
            
        except Exception as e:
            print(f"Error eliminando documentos: {str(e)}")
            return 0
    
    def delete_collection(self):
        """Elimina toda la colección."""
        try:
            self.client.delete_collection("documents")
            # Reinicializar la colección
            self.collection = self.client.get_or_create_collection(
                name="documents",
                embedding_function=None,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            print(f"Error eliminando colección: {str(e)}")