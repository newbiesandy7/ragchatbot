from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from typing import List

app = FastAPI(title="Local Nomic Embedding Service")

# Load the model locally on CPU
print("Loading Nomic Embed model...")
model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True)
print("Model loaded successfully!")

class EmbeddingRequest(BaseModel):
    texts: List[str]

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]

@app.post("/embed", response_model=EmbeddingResponse)
async def get_embeddings(request: EmbeddingRequest):
    formatted_texts = [f"search_document: {text}" for text in request.texts]
    embeddings = model.encode(formatted_texts, convert_to_tensor=False).tolist()
    return {"embeddings": embeddings}

@app.get("/health")
async def health():
    return {"status": "ok"}