import redis
import numpy as np
from sentence_transformers import SentenceTransformer

r = redis.Redis(host="localhost", port=6379)
model = SentenceTransformer("all-MiniLM-L6-v2")


# 🔍 Recherche hybride (vector + filtres)
def search(query, k=10, filters=None):
    vec = model.encode(query, normalize_embeddings=True)
    vec = np.array(vec, dtype=np.float32).tobytes()

    filter_parts = []

    if filters:
        if "segment" in filters:
            filter_parts.append(f"@segment:{{{filters['segment']}}}")

        if "contract_type" in filters:
            filter_parts.append(f"@contract_types:{{{filters['contract_type']}}}")

    base_query = " ".join(filter_parts) if filter_parts else "*"

    query_str = f"{base_query}=>[KNN {k} @embedding $vec AS score]"

    print("REDIS QUERY:", query_str)

    res = r.execute_command(
        "FT.SEARCH", "idx:docs",
        query_str,
        "PARAMS", "4", "vec", vec, "EF_RUNTIME", "100",
        "SORTBY", "score",
        "RETURN", "3", "content", "client_id", "score",
        "DIALECT", "2"
    )

    return res

LIMIT = 100

# 🔥 requête directe (sans RAG)
def get_clients_by_contract_type(contract_type):
    res = r.execute_command(
        "FT.SEARCH", "idx:docs",
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

    return list(set(clients)) 

def get_client_by_name(name):
    res = r.execute_command(
        "FT.SEARCH", "idx:docs",
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

    return doc # unique

def search_by_name(name):
    res = r.execute_command(
        "FT.SEARCH", "idx:docs",
        f'@name:{name}',
        "RETURN", "3", "content", "client_id", "name"
    )
    return res