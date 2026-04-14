import json
import redis
import numpy as np
from sentence_transformers import SentenceTransformer
from collections import defaultdict
from tqdm import tqdm
import orjson
import time

start = time.time()

r = redis.Redis(host="localhost", port=6379, decode_responses=False)

model = SentenceTransformer("intfloat/e5-small-v2")
model.max_seq_length = 256

BATCH_SIZE = 1024


# 🔥 build texte amélioré (plus structuré pour embeddings)
def build_text(client, contracts):
    text = f"passage: Client {client['name']}, {client['age']} ans, {client['city']}, segment {client['segment']}.\n"
    for c in contracts:
        text += f"Contrat TYPE={c['type']} montant={c['amount']} statut={c['status']}.\n"
    return text


def embed_batch(texts):
    return model.encode(texts, batch_size=128, show_progress_bar=False)


# 🔹 Charger contrats
contracts_by_client = defaultdict(list)

with open("contracts.jsonl") as f:
    for line in f:
        c = orjson.loads(line)
        contracts_by_client[c["client_id"]].append(c)


pipe = r.pipeline(transaction=False)

# 🔹 buffers batch
texts = []
keys = []
segments = []
client_ids = []
contract_types_list = []  # 🔥 NOUVEAU

MAX_DOCS = 10000
count = 0
names = []
with open("clients.jsonl") as f:
    for line in f:
        if count >= MAX_DOCS:
            break

        client = orjson.loads(line)
        names.append(client["name"])
        count += 1
        client_id = client["client_id"]

        contracts = contracts_by_client.get(client_id, [])
        text = build_text(client, contracts)

        # 🔥 récupérer types de contrats
        contract_types = list(set([c["type"] for c in contracts]))

        texts.append(text)
        keys.append(f"doc:{client_id}")
        segments.append(client["segment"])
        client_ids.append(client_id)

        # 🔥 TAG Redis format correct
        contract_types_list.append("|".join(contract_types))

        # 🔥 batch plein
        if len(texts) == BATCH_SIZE:

            embeddings = embed_batch(texts)

            for i in range(len(texts)):
                emb = np.array(embeddings[i], dtype=np.float32).tobytes()

                pipe.hset(keys[i], mapping={
                    "client_id": client_ids[i],
                    "name": names[i], # 🔥 stocker aussi le nom pour debug
                    "content": texts[i],
                    "embedding": emb,
                    "segment": segments[i],
                    "contract_types": contract_types_list[i]  # 🔥 AJOUT CRITIQUE
                })

            pipe.execute()

            # reset
            texts, keys, segments, client_ids, contract_types_list = [], [], [], [], []


# 🔹 dernier batch
if texts:
    embeddings = embed_batch(texts)

    for i in range(len(texts)):
        emb = np.array(embeddings[i], dtype=np.float32).tobytes()

        pipe.hset(keys[i], mapping={
            "client_id": client_ids[i],
            "name": names[i],
            "content": texts[i],
            "embedding": emb,
            "segment": segments[i],
            "contract_types": contract_types_list[i]  # 🔥 AJOUT
        })

    pipe.execute()


end = time.time()
print(f"Total time: {end - start:.4f}s")