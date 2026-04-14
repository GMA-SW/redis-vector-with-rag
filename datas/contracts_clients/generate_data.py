import json
import random
from faker import Faker

fake = Faker()

NB_CLIENTS = 1000000
OUTPUT_CLIENTS = "clients.jsonl"
OUTPUT_CONTRACTS = "contracts.jsonl"

contract_types = ["assurance_vie", "credit", "epargne", "auto"]

with open(OUTPUT_CLIENTS, "w") as fc, open(OUTPUT_CONTRACTS, "w") as fct:
    for i in range(NB_CLIENTS):
        client_id = f"C{i}"

        client = {
            "client_id": client_id,
            "name": fake.name(),
            "age": random.randint(18, 80),
            "city": fake.city(),
            "segment": random.choice(["standard", "premium", "vip"])
        }

        fc.write(json.dumps(client) + "\n")

        # 1 à 3 contrats
        for j in range(random.randint(1, 3)):
            contract = {
                "contract_id": f"CTR_{i}_{j}",
                "client_id": client_id,
                "type": random.choice(contract_types),
                "amount": random.randint(1000, 200000),
                "status": random.choice(["actif", "clos"])
            }

            fct.write(json.dumps(contract) + "\n")