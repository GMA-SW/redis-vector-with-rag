import time
import redis
import numpy as np
import orjson

from sentence_transformers import SentenceTransformer
from collections import defaultdict


# =========================================================
# CONFIGURATION
# =========================================================
REDIS_HOST = "localhost"
REDIS_PORT = 6379

CLIENTS_FILE = "clients.jsonl"
CONTRACTS_FILE = "contracts.jsonl"

MODEL_NAME = "intfloat/e5-small-v2"
MAX_SEQ_LENGTH = 256

BATCH_SIZE = 1024
EMBED_BATCH_SIZE = 128
MAX_DOCS = 10000


# =========================================================
# INIT
# =========================================================
start = time.time()

r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=False
)

model = SentenceTransformer(MODEL_NAME)
model.max_seq_length = MAX_SEQ_LENGTH


# =========================================================
# TEXT BUILDER
# =========================================================
def build_text(client, contracts):
    text = f"passage: Client {client['name']}, {client['age']} ans, {client['city']}, segment {client['segment']}.\n"

    for c in contracts:
        text += f"Contrat TYPE={c['type']} montant={c['amount']} statut={c['status']}.\n"

    return text


# =========================================================
# EMBEDDING
# =========================================================
def embed_batch(texts):
    return model.encode(
        texts,
        batch_size=EMBED_BATCH_SIZE,
        show_progress_bar=False
    )


# =========================================================
# DATA LOADING
# =========================================================
def load_contracts():
    contracts_by_client = defaultdict(list)

    with open(CONTRACTS_FILE) as f:
        for line in f:
            c = orjson.loads(line)
            contracts_by_client[c["client_id"]].append(c)

    return contracts_by_client


# =========================================================
# REDIS INGEST (PIPELINE)
# =========================================================
def ingest():
    contracts_by_client = load_contracts()

    pipe = r.pipeline(transaction=False)

    # buffers batch
    texts = []
    keys = []
    segments = []
    client_ids = []
    contract_types_list = []
    names = []

    count = 0

    with open(CLIENTS_FILE) as f:
        for line in f:
            if count >= MAX_DOCS:
                break

            client = orjson.loads(line)
            count += 1

            client_id = client["client_id"]
            contracts = contracts_by_client.get(client_id, [])

            text = build_text(client, contracts)

            # récupérer types contrats
            contract_types = list(set([c["type"] for c in contracts]))

            # buffers
            texts.append(text)
            keys.append(f"doc:{client_id}")
            segments.append(client["segment"])
            client_ids.append(client_id)
            names.append(client["name"])
            contract_types_list.append("|".join(contract_types))

            # -------------------------------------------------
            # FLUSH BATCH
            # -------------------------------------------------
            if len(texts) == BATCH_SIZE:
                flush_batch(
                    pipe,
                    texts,
                    keys,
                    segments,
                    client_ids,
                    names,
                    contract_types_list
                )

                texts, keys, segments, client_ids, contract_types_list, names = [], [], [], [], [], []

    # -----------------------------------------------------
    # FINAL FLUSH
    # -----------------------------------------------------
    if texts:
        flush_batch(
            pipe,
            texts,
            keys,
            segments,
            client_ids,
            names,
            contract_types_list
        )


def flush_batch(pipe, texts, keys, segments, client_ids, names, contract_types_list):
    embeddings = embed_batch(texts)

    for i in range(len(texts)):
        emb = np.array(embeddings[i], dtype=np.float32).tobytes()

        pipe.hset(keys[i], mapping={
            "client_id": client_ids[i],
            "name": names[i],
            "content": texts[i],
            "embedding": emb,
            "segment": segments[i],
            "contract_types": contract_types_list[i]
        })

    pipe.execute()


# =========================================================
# ENTRYPOINT
# =========================================================
if __name__ == "__main__":
    ingest()

    end = time.time()
    print(f"Total time: {end - start:.4f}s")