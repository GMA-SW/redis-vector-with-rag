import redis
import os
import json
import requests
import numpy as np
from sentence_transformers import SentenceTransformer

def get_redis_client():
    return redis.Redis(host="localhost", port=6379)

def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

def create_index(r):
    try:
        r.execute_command(
            "FT.CREATE", "idx:docs",
            "ON", "HASH",
            "PREFIX", "1", "doc:",
            "SCHEMA",
            "content", "TEXT",
            "embedding", "VECTOR", "FLAT", "6",
            "TYPE", "FLOAT32",
            "DIM", "384",
            "DISTANCE_METRIC", "COSINE"
        )
        print("Index créé")
    except:
        print("Index déjà existant")

def bike_to_text(bike):
    return f"""
    Marque: {bike['brand']}
    Modèle: {bike['model']}
    Type: {bike['type']}
    Prix: {bike['price']}
    Description: {bike['description']}
    """

def load_data():
    URL = "https://raw.githubusercontent.com/bsbodden/redis_vss_getting_started/main/data/bikes.json"
    if os.path.exists("bikes.json"):
        with open("bikes.json") as f:
            return json.load(f)

    response = requests.get(URL)
    bikes = response.json()

    with open("bikes.json", "w") as f:
        json.dump(bikes, f)

    return bikes

def ingest(r, model, bikes):
    texts = [bike_to_text(b) for b in bikes]
    embeddings = model.encode(texts)

    for i, (text, emb) in enumerate(zip(texts, embeddings)):
        r.hset(f"doc:{i}", mapping={
            "content": text,
            "embedding": np.array(emb, dtype=np.float32).tobytes()
        })

    print("Bikes indexés")

if __name__ == "__main__":
    r = get_redis_client()
    model = load_model()
    create_index(r)
    bikes = load_data()
    ingest(r, model, bikes)