import time
import numpy as np
import redis
from sentence_transformers import SentenceTransformer

r = redis.Redis(host="localhost", port=6379)
model = SentenceTransformer("all-MiniLM-L6-v2")

queries = [
    "clients avec assurance vie",
    "clients premium avec crédit",
    "contrats actifs",
    "clients avec épargne",
    "clients VIP"
]

def search(query):
    vec = model.encode(query)
    vec = np.array(vec, dtype=np.float32).tobytes()

    start = time.time()

    res = r.execute_command(
        "FT.SEARCH", "idx:docs",
        "*=>[KNN 5 @embedding $vec AS score]",
        "PARAMS", "2", "vec", vec,
        "SORTBY", "score",
        "RETURN", "1", "content",
        "DIALECT", "2"
    )

    duration = time.time() - start

    return res, duration


times = []

for q in queries:
    res, t = search(q)
    times.append(t)

    print(f"\nQuery: {q}")
    print(f"Time: {t:.4f}s")

    for i in range(2, len(res), 2):
        print("-", res[i][1].decode()[:100])

print("\n--- STATS ---")
print(f"Avg latency: {sum(times)/len(times):.4f}s")
print(f"Max latency: {max(times):.4f}s")