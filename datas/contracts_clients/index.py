# =========================================================
# IMPORTS
# =========================================================
import redis


# =========================================================
# CONFIGURATION
# =========================================================
REDIS_HOST = "localhost"
REDIS_PORT = 6379

INDEX_NAME = "idx:docs"
PREFIX = "doc:"


# =========================================================
# INIT
# =========================================================
r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)


# =========================================================
# INDEX CREATION
# =========================================================
def create_index():
    try:
        r.execute_command(
            "FT.CREATE", INDEX_NAME,
            "ON", "HASH",
            "PREFIX", "1", PREFIX,
            "SCHEMA",

            # champs texte
            "content", "TEXT",
            "name", "TEXT",
            "client_id", "TEXT",

            # metadata
            "segment", "TAG",
            "contract_types", "TAG", "SEPARATOR", "|",

            # vecteur
            "embedding", "VECTOR", "HNSW", "6",
            "TYPE", "FLOAT32",
            "DIM", "384",
            "DISTANCE_METRIC", "COSINE",
            "M", "16",
            "EF_CONSTRUCTION", "200"
        )

        print("Index créé avec succès")

    except Exception as e:
        if "Index already exists" in str(e):
            print("Index déjà existant")
        else:
            print("Erreur lors de la création de l'index :", e)

# =========================================================
# OPTIONAL: INFO
# =========================================================
def index_info():
    try:
        info = r.execute_command("FT.INFO", INDEX_NAME)
        print(info)
    except Exception as e:
        print("Erreur FT.INFO :", e)


# =========================================================
# ENTRYPOINT
# =========================================================
if __name__ == "__main__":
    create_index()
    index_info()