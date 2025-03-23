# test_processor.py
import asyncio
from app.services.document_processor import DocumentProcessor

async def test():
    with open("test_document.pdf", "rb") as f:
        file_content = f.read()
    
    from fastapi import UploadFile
    file = UploadFile(filename="test_document.pdf", file=BytesIO(file_content))
    content, path, summary = await DocumentProcessor.process_document(file, user_id=1)
    print(f"Contenido extraído: {content[:100]}...")
    print(f"Resumen: {summary}")

asyncio.run(test())