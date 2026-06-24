from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import CrossEncoder
from typing import List, Dict

app = FastAPI(title="Local BGE Reranker Service")

print("Loading BGE Reranker model...")
# Switched to the un-gated BAAI BGE model for smoother local execution
model = CrossEncoder("BAAI/bge-reranker-base")
print("Reranker model loaded successfully!")

class RerankRequest(BaseModel):
    query: str
    documents: List[str]

class RerankResponse(BaseModel):
    results: List[Dict]

@app.post("/rerank", response_model=RerankResponse)
async def rerank(request: RerankRequest):
    pairs = [[request.query, doc] for doc in request.documents]
    scores = model.predict(pairs).tolist()
    
    results = [
        {"document": doc, "score": score, "index": idx}
        for idx, (doc, score) in enumerate(zip(request.documents, scores))
    ]
    results.sort(key=lambda x: x["score"], reverse=True)
    
    return {"results": results}

@app.get("/health")
async def health():
    return {"status": "ok"}