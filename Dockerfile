FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema y herramientas de Google Cloud
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    gnupg \
    && curl -sSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - \
    && echo "deb https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && apt-get update && apt-get install -y google-cloud-sdk \
    && rm -rf /var/lib/apt/lists/*

# Copiar proyecto
COPY . .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r app/requirements.txt

# Crear directorios necesarios
RUN mkdir -p uploads vector_db

# Exponer puerto
EXPOSE 8000

# Ejecutar aplicación
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]