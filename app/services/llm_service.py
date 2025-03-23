# app/services/llm_service.py
import os
from typing import List, Dict, Any
import json
import requests
from fastapi import HTTPException
from app.core.config import settings
from google.cloud import aiplatform
from google.oauth2 import service_account

class LLMService:
    def __init__(self):
        '''try:
            # Configurar credenciales para la API de Google
            self.project_id = os.environ.get("GOOGLE_PROJECT_ID", settings.GOOGLE_PROJECT_ID)
            self.location = os.environ.get("GOOGLE_LOCATION", settings.GOOGLE_LOCATION)
            self.model_id = os.environ.get("GOOGLE_MODEL_ID", settings.GOOGLE_MODEL_ID)
            
            # Inicializar cliente de Vertex AI si se proporcionan credenciales
            if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                credentials = service_account.Credentials.from_service_account_file(
                    os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
                )
                self.client = aiplatform.gapic.PredictionServiceClient(credentials=credentials)
            else:
                self.client = aiplatform.gapic.PredictionServiceClient()
                
            # Endpoint para el modelo
            self.endpoint = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.model_id}"
            
            print(f"Conectando a Google Flash API en: {self.endpoint}")
            
        except Exception as e:
            print(f"Error de inicialización de Google Flash API: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"No se pudo conectar al servicio LLM. Error: {str(e)}"
            )'''
        
        if os.environ.get("USE_MOCK_LLM", "false").lower() == "true":
            self._use_mock = True
            print("Usando LLM mock para desarrollo local")
        else:
            self._use_mock = False
            # Inicialización normal de Google Flash API

    async def generate_summary(self, content: str) -> str:
        """Genera un resumen del contenido utilizando Google Flash."""
        try:
            prompt = f"""Genera un resumen conciso del siguiente texto. El resumen debe incluir los puntos clave, 
            pero ser significativamente más corto que el texto original.
            
            TEXTO A RESUMIR:
            {content}
            
            RESUMEN:"""
            
            response = self._call_flash_api(prompt, temperature=0.2, max_tokens=250)
            return response
            
        except Exception as e:
            print(f"Error generando resumen: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Error al generar el resumen: {str(e)}"
            )

    async def answer_question(self, context: str, question: str) -> str:
        """Responde una pregunta basada en el contexto proporcionado."""
        try:
            prompt = f"""Responde la siguiente pregunta utilizando solo la información proporcionada en el CONTEXTO.
            Si la respuesta no está en el CONTEXTO, indica que no puedes responder basado en la información proporcionada.
            
            CONTEXTO:
            {context}
            
            PREGUNTA:
            {question}
            
            RESPUESTA:"""
            
            response = self._call_flash_api(prompt, temperature=0.3, max_tokens=500)
            return response
            
        except Exception as e:
            print(f"Error respondiendo pregunta: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Error al responder la pregunta: {str(e)}"
            )
            
    async def answer_question_with_sources(self, question: str, relevant_chunks: List[Dict[str, Any]]) -> str:
        """Responde una pregunta utilizando trozos relevantes de documentos con citación de fuentes."""
        try:
            context = ""
            sources = []
            
            # Preparar los chunks y sus fuentes
            for i, chunk in enumerate(relevant_chunks):
                context += f"[CHUNK {i+1}]: {chunk['text']}\n\n"
                sources.append(f"[CHUNK {i+1}]: {chunk['metadata']['source']}, página {chunk['metadata'].get('page', 'N/A')}")
            
            prompt = f"""Responde la siguiente pregunta utilizando solo la información proporcionada en los CHUNKS.
            Si la respuesta no está en los CHUNKS, indica que no puedes responder basado en la información proporcionada.
            Cita los números de chunk que utilizaste para construir tu respuesta (ejemplo: [CHUNK 1], [CHUNK 3]).
            
            CHUNKS:
            {context}
            
            PREGUNTA:
            {question}
            
            RESPUESTA:"""
            
            response = self._call_flash_api(prompt, temperature=0.3, max_tokens=800)
            
            # Añadir las fuentes al final de la respuesta
            if sources:
                response += "\n\nFuentes:\n" + "\n".join(sources)
                
            return response
            
        except Exception as e:
            print(f"Error respondiendo pregunta con fuentes: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"Error al responder la pregunta: {str(e)}"
            )

    def _call_flash_api(self, prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
        """Realiza la llamada a la API de Google Flash."""
        if os.environ.get("USE_MOCK_LLM", "false").lower() == "true":
            print(f"MOCK LLM: {prompt[:50]}...")
            # Return mock response based on prompt
            if "generar un resumen" in prompt.lower():
                return "Este es un resumen generado por el LLM simulado para desarrollo local."
            else:
                return "Esta es una respuesta simulada para desarrollo local. En producción, se utilizará Google Flash API."
        else:
            try:
                instance = {
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                    "top_p": 0.8,
                    "top_k": 40
                }
                
                instances = [instance]
                
                response = self.client.predict(
                    endpoint=self.endpoint,
                    instances=[instances]
                )
                
                # Extraer el texto de la respuesta
                predictions = response.predictions
                if predictions and len(predictions) > 0:
                    result = predictions[0]
                    # Dependiendo de la estructura de la respuesta, podría necesitar ajustes
                    if isinstance(result, dict) and "content" in result:
                        return result["content"]
                    elif isinstance(result, str):
                        return result
                    else:
                        return str(result)
                else:
                    return "No se pudo generar una respuesta."
                    
            except Exception as e:
                print(f"Error llamando a Flash API: {str(e)}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Error comunicándose con Flash API: {str(e)}"
                )