#!/usr/bin/env python3
"""
Script para generar un archivo de credenciales de ejemplo para desarrollo local.
NOTA: Este archivo es SOLO para desarrollo y pruebas locales.
Para producción, usa credenciales reales de Google Cloud.
"""

import json
import os
import sys
import uuid
from datetime import datetime, timedelta

def generate_mock_credentials():
    """Genera credenciales falsas para desarrollo local con USE_MOCK_LLM=true"""
    
    # Crear estructura de credenciales de ejemplo
    credentials = {
        "type": "service_account",
        "project_id": "mock-project-id",
        "private_key_id": str(uuid.uuid4()),
        "private_key": "-----BEGIN PRIVATE KEY-----\nMOCK_KEY_FOR_DEVELOPMENT_ONLY\n-----END PRIVATE KEY-----\n",
        "client_email": "mock-service-account@mock-project-id.iam.gserviceaccount.com",
        "client_id": str(uuid.uuid4()),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mock-service-account%40mock-project-id.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }
    
    # Guardar credenciales en el archivo
    with open("credentials.json", "w") as f:
        json.dump(credentials, f, indent=2)
    
    print("Archivo de credenciales mock generado: credentials.json")
    print("ADVERTENCIA: Este archivo es SOLO para desarrollo local con USE_MOCK_LLM=true")
    print("Para producción, usa credenciales reales de Google Cloud.")

if __name__ == "__main__":
    # Verificar si el archivo ya existe
    if os.path.exists("credentials.json"):
        response = input("El archivo credentials.json ya existe. ¿Sobrescribir? (s/n): ")
        if response.lower() != 's':
            print("Operación cancelada.")
            sys.exit(0)
    
    generate_mock_credentials()
    
    # Sugerir actualizar las variables de entorno
    print("\nRecuerda configurar tus variables de entorno en .env:")
    print("GOOGLE_PROJECT_ID=mock-project-id")
    print("GOOGLE_LOCATION=us-central1")
    print("GOOGLE_MODEL_ID=flash")
    print("USE_MOCK_LLM=true  # Para desarrollo local sin Google Cloud")