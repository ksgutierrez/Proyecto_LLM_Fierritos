from google.cloud import aiplatform

# Inicializar Vertex AI
aiplatform.init(
    project="neon-chimera-454920-c1",
    location="us-east1",
    credentials="credentials.json",
)

# Probar el modelo de incrustación
response = aiplatform.TextEmbeddingModel.from_pretrained("textembedding-gecko@latest").get_embeddings(["Hola, mundo!"])
print(response)