# app/services/llm_service.py
import os
from typing import List, Dict, Any
from fastapi import HTTPException
from google.cloud import aiplatform
from google.oauth2 import service_account

class LLMService:
    def __init__(self):
        # Check if we're using mock mode
        self._use_mock = os.environ.get("USE_MOCK_LLM", "false").lower() == "true"
        
        if not self._use_mock:
            try:
                # Initialize Google Cloud client
                from google.cloud import aiplatform
                from google.oauth2 import service_account
                
                self.project_id = os.environ.get("GOOGLE_PROJECT_ID")
                self.location = os.environ.get("GOOGLE_LOCATION", "us-central1")
                self.model_id = os.environ.get("GOOGLE_MODEL_ID", "flash")
                
                # Initialize client only if not in mock mode
                if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                    credentials = service_account.Credentials.from_service_account_file(
                        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
                    )
                    self.client = aiplatform.gapic.PredictionServiceClient(credentials=credentials)
                else:
                    self.client = aiplatform.gapic.PredictionServiceClient()
                    
                self.endpoint = f"projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.model_id}"
                print(f"Conectando a Google Flash API en: {self.endpoint}")
            except Exception as e:
                print(f"Error inicializando Google Cloud: {str(e)}")
                self._use_mock = True
                print("Activando modo mock debido a error de inicialización")

    async def generate_summary(self, content: str) -> str:
        try:
            prompt = f"""Genera un resumen conciso del siguiente texto:
            
            TEXTO:
            {content}
            
            RESUMEN:"""
            
            response = self._call_flash_api(prompt, temperature=0.2, max_tokens=250)
            return response
        except Exception as e:
            print(f"Error generando resumen: {str(e)}")
            return "Error al generar resumen. Usando resumen alternativo."

    async def answer_question(self, context: str, question: str) -> str:
        try:
            prompt = f"""Responde la siguiente pregunta basándote en el contexto:
            
            CONTEXTO:
            {context}
            
            PREGUNTA:
            {question}
            
            RESPUESTA:"""
            
            response = self._call_flash_api(prompt, temperature=0.3, max_tokens=500)
            return response
        except Exception as e:
            print(f"Error respondiendo pregunta: {str(e)}")
            return f"No se pudo responder la pregunta debido a un error: {str(e)}"

    async def answer_question_with_sources(self, question: str, relevant_chunks: List[Dict[str, Any]]) -> str:
        try:
            context = ""
            for i, chunk in enumerate(relevant_chunks):
                context += f"[CHUNK {i+1}]: {chunk['text']}\n\n"
            
            prompt = f"""Responde basándote solo en estos fragmentos:
            
            FRAGMENTOS:
            {context}
            
            PREGUNTA:
            {question}
            
            RESPUESTA:"""
            
            response = self._call_flash_api(prompt, temperature=0.3, max_tokens=800)
            return response
        except Exception as e:
            print(f"Error respondiendo con fuentes: {str(e)}")
            return f"No se pudo responder la pregunta con fuentes debido a un error: {str(e)}"

    def _call_flash_api(self, prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
        """Realiza la llamada a la API o genera respuesta simulada"""
        if self._use_mock:
            print(f"[MOCK] Procesando prompt: {prompt[:50]}...")
            # Generar respuesta simulada
            if "resumen" in prompt.lower():
                return "Este es un resumen generado por el servicio MOCK para desarrollo local."
            elif "pregunta" in prompt.lower():
                return "Esta es una respuesta simulada para la pregunta. En producción, esto sería generado por Google Flash API."
            else:
                return "Respuesta simulada de LLM para desarrollo local."
        else:
            # Implementación real de llamada a API
            try:
                instance = {
                    "prompt": prompt,
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
                
                response = self.client.predict(
                    endpoint=self.endpoint,
                    instances=[instance]
                )
                
                return response.predictions[0]
            except Exception as e:
                print(f"Error llamando a Flash API: {str(e)}")
                raise HTTPException(
                    status_code=503, 
                    detail=f"Error comunicándose con Flash API: {str(e)}"
                )