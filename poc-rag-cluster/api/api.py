import redis
import os
import requests
import numpy as np
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI

app = FastAPI()

r = redis.Redis( host=os.getenv("REDIS_HOST", "redis-stack"), port=int(os.getenv("REDIS_PORT", 6379)), decode_responses=False)
model = SentenceTransformer("all-MiniLM-L6-v2")

def ask_llm(prompt):
    response = requests.post(
        "http://ollama:11434/api/generate",
        json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )
    return response.json()["response"]

def search(r, model, query, k=3):
    query_vec = model.encode(query)

    res = r.execute_command(
        "FT.SEARCH", "idx:docs",
        f"*=>[KNN {k} @embedding $vec AS score]",
        "PARAMS", "2", "vec", np.array(query_vec, dtype=np.float32).tobytes(),
        "SORTBY", "score",
        "RETURN", "1", "content",
        "DIALECT", "2"
    )

    contexts = []
    for i in range(2, len(res), 2):
        val = res[i][1]
        if isinstance(val, bytes):
            val = val.decode("utf-8")
        contexts.append(val)
    return contexts

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

@app.get("/ask")
def ask(query: str):
    contexts = search(r, model, query)
    answer = generate_answer(contexts, query)
    return {
        "query": query,
        "contexts": contexts,
        "answer": answer
    }