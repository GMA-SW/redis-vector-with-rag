import os
import json
import requests
import redis
import numpy as np

from sentence_transformers import SentenceTransformer


# =========================================================
# CONFIGURATION
# =========================================================
REDIS_HOST = "localhost"
REDIS_PORT = 6379

INDEX_NAME = "idx:docs"
PREFIX = "doc:"

MODEL_NAME = "all-MiniLM-L6-v2"
VECTOR_DIM = 384

DATA_URL = "https://raw.githubusercontent.com/bsbodden/redis_vss_getting_started/main/data/bikes.json"
LOCAL_FILE = "bikes.json"


# =========================================================
# INIT
# =========================================================
def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT)


def load_model():
    return SentenceTransformer(MODEL_NAME)


# =========================================================
# INDEX MANAGEMENT
# =========================================================
def create_index(r):
    try:
        r.execute_command(
            "FT.CREATE", INDEX_NAME,
            "ON", "HASH",
            "PREFIX", "1", PREFIX,
            "SCHEMA",
            "content", "TEXT",
            "embedding", "VECTOR", "FLAT", "6",
            "TYPE", "FLOAT32",
            "DIM", str(VECTOR_DIM),
            "DISTANCE_METRIC", "COSINE"
        )
        print("Index créé")

    except:
        print("Index déjà existant")


# =========================================================
# DATA LOADING
# =========================================================
def load_data():
    # ---- local ----
    if os.path.exists(LOCAL_FILE):
        with open(LOCAL_FILE) as f:
            return json.load(f)

    # ---- remote ----
    response = requests.get(DATA_URL)
    bikes = response.json()

    with open(LOCAL_FILE, "w") as f:
        json.dump(bikes, f)

    return bikes


# =========================================================
# TEXT TRANSFORMATION
# =========================================================
def bike_to_text(bike):
    return f"""
    Marque: {bike['brand']}
    Modèle: {bike['model']}
    Type: {bike['type']}
    Prix: {bike['price']}
    Description: {bike['description']}
    """


# =========================================================
# INGEST
# =========================================================
def ingest(r, model, bikes):
    texts = [bike_to_text(b) for b in bikes]
    embeddings = model.encode(texts)

    for i, (text, emb) in enumerate(zip(texts, embeddings)):
        r.hset(f"{PREFIX}{i}", mapping={
            "content": text,
            "embedding": np.array(emb, dtype=np.float32).tobytes()
        })

    print("Bikes indexés")


# =========================================================
# ENTRYPOINT
# =========================================================
if __name__ == "__main__":
    r = get_redis_client()
    model = load_model()

    create_index(r)

    bikes = load_data()
    ingest(r, model, bikes)