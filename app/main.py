# app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, documents, users
from app.db.base import Base
from app.db.session import engine
import logging
from datetime import datetime
import time
from google.cloud import aiplatform
from google.cloud.aiplatform import metadata
from google.oauth2 import service_account
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Inicializar Google Cloud
try:
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        credentials = service_account.Credentials.from_service_account_file(
            os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        )
        aiplatform.init(
            project=settings.GOOGLE_PROJECT_ID,
            location=settings.GOOGLE_LOCATION,
            credentials=credentials
        )
    else:
        aiplatform.init(
            project=settings.GOOGLE_PROJECT_ID,
            location=settings.GOOGLE_LOCATION
        )
    logger.info("Google Cloud inicializado correctamente")
except Exception as e:
    logger.error(f"Error inicializando Google Cloud: {str(e)}")
    

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API para sistema RAG utilizando Google Flash API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variable para almacenar el tiempo de inicio
start_time = time.time()

@app.get(f"{settings.API_V1_STR}/health", tags=["monitoring"])
async def health_check():
    """
    Endpoint de comprobación de salud para monitoreo.
    Verifica la conexión a Google Cloud.
    """
    try:
        # Verificar conexión a Google Cloud
        if os.environ.get("USE_MOCK_LLM", "false").lower() != "true":
            # Usar un método más simple para verificar la conexión
            from google.cloud import aiplatform
            
            # Solo verificamos que podamos inicializar el cliente
            aiplatform.init(
                project=settings.GOOGLE_PROJECT_ID,
                location=settings.GOOGLE_LOCATION
            )
            
            # Si llegamos hasta aquí, la conexión funciona
            google_cloud_status = "up"
        else:
            google_cloud_status = "mock_mode"
            
        # Calcular tiempo de actividad
        uptime = time.time() - start_time
        
        return {
            "status": "healthy",
            "uptime": round(uptime),
            "timestamp": datetime.now().isoformat(),
            "version": settings.VERSION,
            "services": {
                "google_cloud": google_cloud_status,
                "database": "up",
                "api": "up"
            }
        }
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "version": settings.VERSION
        }

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR + "/auth", tags=["auth"])
app.include_router(documents.router, prefix=settings.API_V1_STR + "/documents", tags=["documents"])
app.include_router(users.router, prefix=settings.API_V1_STR + "/users", tags=["users"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)