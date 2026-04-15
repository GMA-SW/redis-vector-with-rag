# ================================
# IMPORTS
# ================================
import os
import redis
import requests
import numpy as np
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI


# ================================
# CONFIGURATION
# ================================
REDIS_HOST = os.getenv("REDIS_HOST", "redis-stack")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
OLLAMA_URL = "http://ollama:11434/api/generate"
MODEL_NAME = "all-MiniLM-L6-v2"
INDEX_NAME = "idx:docs"


# ================================
# INITIALISATION
# ================================
app = FastAPI()

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=False
)

model = SentenceTransformer(MODEL_NAME)


# ================================
# LLM
# ================================
def ask_llm(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )
    return response.json()["response"]


# ================================
# REDIS SEARCH
# ================================
def search(query, k=3):
    query_vec = model.encode(query)
    query_vec = np.array(query_vec, dtype=np.float32).tobytes()

    res = r.execute_command(
        "FT.SEARCH", INDEX_NAME,
        f"*=>[KNN {k} @embedding $vec AS score]",
        "PARAMS", "2", "vec", query_vec,
        "SORTBY", "score",
        "RETURN", "1", "content",
        "DIALECT", "2"
    )

    return parse_results(res)


def parse_results(res):
    contexts = []

    for i in range(2, len(res), 2):
        val = res[i][1]

        if isinstance(val, bytes):
            val = val.decode("utf-8")

        contexts.append(val)

    return contexts


# ================================
# RAG PIPELINE
# ================================
def generate_answer(contexts, query):
    context_text = "\n".join(contexts)

    prompt = f"""
Tu es un expert en vélos.

Utilise uniquement le contexte pour répondre.

Contexte:
{context_text}

Question:
{query}
"""

    return ask_llm(prompt)


def rag_pipeline(query):
    contexts = search(query)
    answer = generate_answer(contexts, query)

    return contexts, answer


# ================================
# API
# ================================
@app.get("/ask")
def ask(query: str):
    contexts, answer = rag_pipeline(query)

    return {
        "query": query,
        "contexts": contexts,
        "answer": answer
    }