# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Fierritos RAG"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database settings
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ragsaas")
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # Authentication
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "secret_key_change_in_prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    
    # Configuración de Google Cloud
    GOOGLE_PROJECT_ID: str = os.getenv("GOOGLE_PROJECT_ID", "")
    GOOGLE_LOCATION: str = os.getenv("GOOGLE_LOCATION", "us-central1")
    GOOGLE_MODEL_ID: str = os.getenv("GOOGLE_MODEL_ID", "flash")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # GCP Compute Engine
    GCP_ZONE: str = os.getenv("GCP_ZONE", "us-central1-a")
    GCP_REGION: str = os.getenv("GCP_REGION", "us-central1")
    
    # Keep Ollama settings for backward compatibility
    OLLAMA_BASE_URL: Optional[str] = None
    OLLAMA_MODEL: Optional[str] = None
    OLLAMA_TIMEOUT: Optional[int] = None
    OLLAMA_MAX_RETRIES: Optional[int] = None
    OLLAMA_RETRY_DELAY: Optional[int] = None
    # Frontend Configuration
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8001")
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:8001",
        "http://localhost:8000",
        "http://localhost:8050"
    ]
    
    # Document processing
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
    
    # ChromaDB settings
    CHROMADB_DIR: str = os.getenv("CHROMADB_DIR", "vector_db")

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
settings.SQLALCHEMY_DATABASE_URI = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_SERVER}/{settings.POSTGRES_DB}"
)