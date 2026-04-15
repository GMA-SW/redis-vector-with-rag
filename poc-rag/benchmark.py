import time
import numpy as np
import redis
from sentence_transformers import SentenceTransformer


# ======================
# CONFIG
# ======================
CONFIG = {
    "redis_host": "localhost",
    "redis_port": 6379,
    "index_name": "idx:docs",
    "model_name": "all-MiniLM-L6-v2",
    "k": 5,
    "ef_runtime": 100
}


# ======================
# EMBEDDER
# ======================
class Embedder:
    def __init__(self, model_name):
        self.model = SentenceTransformer(model_name)

    def encode(self, text):
        vec = self.model.encode(text)
        return np.array(vec, dtype=np.float32).tobytes()


# ======================
# REDIS SEARCH ENGINE
# ======================
class RedisVectorSearch:
    def __init__(self, config):
        self.r = redis.Redis(
            host=config["redis_host"],
            port=config["redis_port"]
        )
        self.index = config["index_name"]
        self.k = config["k"]
        self.ef_runtime = config["ef_runtime"]

    def search(self, vec, filters=None):
        filter_query = "*"

        if filters:
            parts = []
            if "segment" in filters:
                parts.append(f"@segment:{{{filters['segment']}}}")
            if "contract_type" in filters:
                parts.append(f"@contract_types:{{{filters['contract_type']}}}")

            filter_query = " ".join(parts)

        query = f"{filter_query}=>[KNN {self.k} @embedding $vec AS score]"

        start = time.time()

        res = self.r.execute_command(
            "FT.SEARCH", self.index,
            query,
            "PARAMS", "4", "vec", vec, "EF_RUNTIME", str(self.ef_runtime),
            "SORTBY", "score",
            "RETURN", "2", "content", "score",
            "DIALECT", "2"
        )

        latency = time.time() - start

        parsed = self._parse_results(res)

        return {
            "latency": latency,
            "results": parsed
        }

    def _parse_results(self, res):
        docs = []

        for i in range(1, len(res), 2):
            fields = res[i + 1]

            doc = {}
            for j in range(0, len(fields), 2):
                key = fields[j].decode()
                value = fields[j + 1]

                if isinstance(value, bytes):
                    value = value.decode()

                doc[key] = value

            docs.append(doc)

        return docs


# ======================
# BENCHMARK
# ======================
class Benchmark:
    def __init__(self, search_engine, embedder):
        self.search_engine = search_engine
        self.embedder = embedder

    def run(self, queries):
        latencies = []

        for q in queries:
            vec = self.embedder.encode(q)

            result = self.search_engine.search(vec)

            latency = result["latency"]
            docs = result["results"]

            latencies.append(latency)

            print(f"\nQuery: {q}")
            print(f"Latency: {latency:.4f}s")
            print(f"Results: {len(docs)}")

            for d in docs[:3]:
                print("-", d["content"][:100])

        self._print_stats(latencies)

    def _print_stats(self, latencies):
        print("\n--- STATS ---")
        print(f"Avg latency: {np.mean(latencies):.4f}s")
        print(f"Max latency: {np.max(latencies):.4f}s")
        print(f"P95 latency: {np.percentile(latencies, 95):.4f}s")


# ======================
# MAIN
# ======================
if __name__ == "__main__":

    queries = [
        "clients avec assurance vie",
        "clients premium avec crédit",
        "contrats actifs",
        "clients avec épargne",
        "clients VIP"
    ]

    embedder = Embedder(CONFIG["model_name"])
    search_engine = RedisVectorSearch(CONFIG)

    benchmark = Benchmark(search_engine, embedder)
    benchmark.run(queries)