# Fierritos RAG - Sistema de Preguntas y Respuestas con Google Cloud

Sistema de Recuperación Aumentada de Generación (RAG) que utiliza Google Flash API para proporcionar respuestas precisas basadas en documentos cargados por el usuario.

## Características

- **Procesamiento de documentos**: Soporta PDF, DOCX, TXT y Markdown
- **Motor RAG**: Utiliza Google Flash API para respuestas basadas en contexto
- **Embeddings vectoriales**: Implementa Google Text Embedding API para búsqueda semántica
- **Interfaz intuitiva**: Frontend sencillo para subir documentos y hacer preguntas
- **API RESTful**: Endpoints completos para integración con otros sistemas

## Tecnologías utilizadas

- Backend: FastAPI, SQLAlchemy, PostgreSQL
- LLM: Google Flash API (Gemini)
- Embeddings: Google Text Embedding API
- Almacenamiento vectorial: ChromaDB
- Procesamiento asíncrono: Celery, Redis
- Contenedores: Docker, Docker Compose

## Configuración

### Requisitos previos

- Cuenta de Google Cloud con APIs habilitadas:
  - Vertex AI API
  - IAM API
- Archivo de credenciales de Google Cloud (JSON)
- Docker y Docker Compose

### Instrucciones de instalación

1. Clona este repositorio
2. Coloca tu archivo de credenciales como `credentials.json` en el directorio raíz
3. Configura las variables de entorno en `.env`:
