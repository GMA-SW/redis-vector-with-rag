import json
import random
from faker import Faker


# =========================================================
# CONFIGURATION
# =========================================================
NB_CLIENTS = 1_000_000

OUTPUT_CLIENTS = "clients.jsonl"
OUTPUT_CONTRACTS = "contracts.jsonl"

SEGMENTS = ["standard", "premium", "vip"]
CONTRACT_TYPES = ["assurance_vie", "credit", "epargne", "auto"]
CONTRACT_STATUS = ["actif", "clos"]

MIN_CONTRACTS = 1
MAX_CONTRACTS = 3


# =========================================================
# INIT
# =========================================================
fake = Faker()


# =========================================================
# DATA GENERATION
# =========================================================
def generate_client(client_id):
    return {
        "client_id": client_id,
        "name": fake.name(),
        "age": random.randint(18, 80),
        "city": fake.city(),
        "segment": random.choice(SEGMENTS)
    }


def generate_contract(client_id, client_index, contract_index):
    return {
        "contract_id": f"CTR_{client_index}_{contract_index}",
        "client_id": client_id,
        "type": random.choice(CONTRACT_TYPES),
        "amount": random.randint(1000, 200000),
        "status": random.choice(CONTRACT_STATUS)
    }


# =========================================================
# MAIN GENERATION LOOP
# =========================================================
def generate_data():
    with open(OUTPUT_CLIENTS, "w") as fc, open(OUTPUT_CONTRACTS, "w") as fct:

        for i in range(NB_CLIENTS):
            client_id = f"C{i}"

            # ---- client ----
            client = generate_client(client_id)
            fc.write(json.dumps(client) + "\n")

            # ---- contracts ----
            nb_contracts = random.randint(MIN_CONTRACTS, MAX_CONTRACTS)

            for j in range(nb_contracts):
                contract = generate_contract(client_id, i, j)
                fct.write(json.dumps(contract) + "\n")


# =========================================================
# ENTRYPOINT
# =========================================================
if __name__ == "__main__":
    generate_data()