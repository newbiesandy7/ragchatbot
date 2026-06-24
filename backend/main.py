import os
import json
import httpx
import math
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="BIC Campus Chatbot File-DB Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATIONS ---
EMBEDDER_URL = "http://127.0.0.1:8001/embed"
LOCAL_DB_FILE = "campus_knowledge_base.json"
GROQ_API_KEY = "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"  # Substitute your Groq key here

groq_client = Groq(api_key=GROQ_API_KEY)
http_client = httpx.AsyncClient()

class ChatRequest(BaseModel):
    session_id: str
    message: str

def calculate_cosine_similarity(vec_a, vec_b):
    """Calculates dot products over vector lengths natively."""
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if not norm_a or not norm_b:
        return 0.0
    return dot_product / (norm_a * norm_b)

@app.post("/chat")
async def chat_with_docs(request: ChatRequest):
    try:
        # 1. Check if our database file exists
        if not os.path.exists(LOCAL_DB_FILE):
            raise HTTPException(status_code=500, detail="Database file missing. Please run the ingestion script first.")

        # 2. Vectorize user message request
        embed_response = await http_client.post(EMBEDDER_URL, json={"texts": [request.message]})
        embed_response.raise_for_status()
        query_vector = embed_response.json()["embeddings"][0]

        # 3. Read the JSON file and execute manual Cosine Filtering scans
        with open(LOCAL_DB_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)

        scored_records = []
        for record in records:
            score = calculate_cosine_similarity(query_vector, record["vector"])
            scored_records.append({
                "text": record["text"],
                "filename": record["filename"],
                "score": score
            })

        # 4. Filter for top 3 matching elements
        scored_records.sort(key=lambda x: x["score"], reverse=True)
        top_matches = scored_records[:3]

        context = "No specific structural announcement details verified from current campus knowledge maps."
        source_file = "None"

        if top_matches and top_matches[0]["score"] > 0.3:  # Only use content if it's somewhat relevant
            context_blocks = [match["text"] for match in top_matches]
            context = "\n\n---\n\n".join(context_blocks)
            source_urls = list(set([match["filename"] for match in top_matches]))
            source_file = ", ".join(source_urls)

        # 5. Send payload to LLM context window
        system_prompt = """
You are the official student AI assistant for Boston International College (BIC) located in Chitwan, Nepal. 
Answer the user's question accurately, professionally, and warmly using the provided college context block data.

CRITICAL DIRECTIVES:
1. Speak completely naturally. Never use technical phrases like "based on the provided context" or "the text states".
2. If the context contains relevant information, use it to build a helpful response. 
3. If you do not have enough specific course details inside your data window, guide them to contact the BIC administration panel directly.
"""
        
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context Data:\n{context}\n\nUser Question: {request.message}"}
            ],
            temperature=0.2
        )

        return {
            "response": completion.choices[0].message.content,
            "source_used": source_file
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Local-DB query handling crash: {str(e)}")