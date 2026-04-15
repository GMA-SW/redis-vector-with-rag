import redis
import numpy as np
from sentence_transformers import SentenceTransformer


# =========================================================
# CONFIGURATION
# =========================================================
REDIS_HOST = "localhost"
REDIS_PORT = 6379

INDEX_NAME = "idx:docs"

VECTOR_DIM = 384
EF_RUNTIME = 100
LIMIT = 100

MODEL_NAME = "all-MiniLM-L6-v2"


# =========================================================
# INIT CLIENTS
# =========================================================
r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
model = SentenceTransformer(MODEL_NAME)


# =========================================================
# VECTOR UTILS
# =========================================================
def encode_query(query):
    vec = model.encode(query, normalize_embeddings=True)
    return np.array(vec, dtype=np.float32).tobytes()


# =========================================================
# QUERY BUILDERS
# =========================================================
def build_filter_query(filters):
    filter_parts = []

    if not filters:
        return "*"

    if "segment" in filters:
        filter_parts.append(f"@segment:{{{filters['segment']}}}")

    if "contract_type" in filters:
        filter_parts.append(f"@contract_types:{{{filters['contract_type']}}}")

    return " ".join(filter_parts) if filter_parts else "*"


def build_knn_query(base_query, k):
    return f"{base_query}=>[KNN {k} @embedding $vec AS score]"


# =========================================================
# SEARCH (HYBRID VECTOR)
# =========================================================
def search(query, k=10, filters=None):
    vec = encode_query(query)

    base_query = build_filter_query(filters)
    query_str = build_knn_query(base_query, k)

    print("REDIS QUERY:", query_str)

    res = r.execute_command(
        "FT.SEARCH", INDEX_NAME,
        query_str,
        "PARAMS", "4", "vec", vec, "EF_RUNTIME", str(EF_RUNTIME),
        "SORTBY", "score",
        "RETURN", "3", "content", "client_id", "score",
        "DIALECT", "2"
    )

    return res


# =========================================================
# STRUCTURED QUERIES (NO RAG)
# =========================================================
def get_clients_by_contract_type(contract_type):
    res = r.execute_command(
        "FT.SEARCH", INDEX_NAME,
        f"@contract_types:{{{contract_type}}}",
        "RETURN", "1", "client_id",
        "LIMIT", "0", LIMIT
    )

    clients = []

    for i in range(2, len(res), 2):
        try:
            client_id = res[i][1].decode()
            clients.append(client_id)
        except:
            continue

    return list(set(clients))  # unique


def get_client_by_name(name):
    res = r.execute_command(
        "FT.SEARCH", INDEX_NAME,
        f"@name:\"{name}\"",
        "RETURN", "3", "content", "client_id", "name"
    )

    if res[0] == 0:
        return None

    fields = res[2]
    doc = {}

    for i in range(0, len(fields), 2):
        key = fields[i].decode()
        value = fields[i + 1].decode()
        doc[key] = value

    return doc  # unique


def search_by_name(name):
    res = r.execute_command(
        "FT.SEARCH", INDEX_NAME,
        f'@name:{name}',
        "RETURN", "3", "content", "client_id", "name"
    )

    return res