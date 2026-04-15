import time
import re
import requests

from new_search import search, get_clients_by_contract_type, get_client_by_name


# =========================================================
# CONFIGURATION
# =========================================================
OLLAMA_URL = "http://localhost:11434/api/generate"


# =========================================================
# DETECTION (intent / filtre / nom)
# =========================================================
def detect_filter(query):
    q = query.lower()

    if "assurance vie" in q:
        return "assurance_vie"
    if "credit" in q:
        return "credit"
    if "epargne" in q:
        return "epargne"

    return None


def detect_name(query):
    match = re.search(r"[A-Z][a-z]+ [A-Z][a-z]+", query)
    return match.group(0) if match else None


# =========================================================
# LLM
# =========================================================
def ask_llm(prompt):
    try:
        res = requests.post(OLLAMA_URL, json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        })

        if res.status_code != 200:
            print("Erreur LLM:", res.text)
            return "Erreur LLM"

        data = res.json()
        return data.get("response", "Pas de réponse")

    except Exception as e:
        print("Erreur appel LLM:", e)
        return "Erreur technique"


# =========================================================
# REDIS RESULT PARSING
# =========================================================
def parse_results(results):
    contexts = []

    for i in range(1, len(results), 2):
        fields = results[i + 1]

        doc = {}
        for j in range(0, len(fields), 2):
            key = fields[j].decode()
            value = fields[j + 1]

            if isinstance(value, bytes):
                value = value.decode()

            doc[key] = value

        contexts.append(doc.get("content", ""))

    return contexts


# =========================================================
# PROMPT BUILDER
# =========================================================
def build_prompt(context_text, query):
    return f"""
Tu es un système d'extraction de données.

Tu dois répondre UNIQUEMENT avec les informations présentes dans le contexte.

Règles STRICTES :
- N'invente rien
- Ne complète pas
- Si info absente → dire "Non trouvé"

Contexte:
{context_text}

Question:
{query}

Réponse:
"""


# =========================================================
# RAG PIPELINE
# =========================================================
def rag(query):
    contract_type = detect_filter(query)
    name = detect_name(query)

    print("Detected filter:", contract_type)
    print("Detected name:", name)

    # -----------------------------------------------------
    # 1. CAS STRUCTURÉ (requête directe Redis)
    # -----------------------------------------------------
    if "quels clients" in query.lower() and contract_type:
        clients = get_clients_by_contract_type(contract_type)

        if not clients:
            return "Aucun client trouvé."

        return "Clients trouvés : " + ", ".join(clients)

    # -----------------------------------------------------
    # 2. CAS NOM (lookup direct)
    # -----------------------------------------------------
    if name:
        client = get_client_by_name(name)

        if client:
            return client["content"]

        return "Client non trouvé."

    # -----------------------------------------------------
    # 3. RAG CLASSIQUE (vector search)
    # -----------------------------------------------------
    filters = {}
    if contract_type:
        filters["contract_type"] = contract_type

    results = search(query, k=10, filters=filters)
    contexts = parse_results(results)

    if not contexts:
        return "Je ne trouve pas l'information dans les données."

    # 🔥 limitation contexte (important pour LLM)
    contexts = contexts[:5]
    context_text = "\n".join(contexts)

    print("\n--- CONTEXT ---")
    print(context_text[:500])

    prompt = build_prompt(context_text, query)

    return ask_llm(prompt)


# =========================================================
# MAIN (TEST)
# =========================================================
if __name__ == "__main__":
    start = time.time()

    print(rag("Quelle est la moyenne des montants assurés pour les clients de Paris ?"))

    end = time.time()
    print(f"\nTemps d'exécution: {end - start:.2f} secondes")