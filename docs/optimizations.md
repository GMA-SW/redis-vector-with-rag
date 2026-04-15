---
layout: default
title: Optimisations et performance
---

# Optimisations et choix techniques – Redis Vector + RAG

## 1. Vector Search avec Redis

### Description
Utilisation de Redis comme base de données vectorielle pour effectuer du **semantic search** sur des documents clients enrichis.

### Détails techniques
- Embeddings générés via `sentence-transformers` (ex: all-MiniLM-L6-v2, e5-small-v2)
- Stockage en `FLOAT32` (4 bytes par dimension)
- Dimension typique : `384`
- Requêtes via KNN :
```sql
*=>[KNN 10 @embedding $vec AS score]
```
- Distance utilisée : COSINE

### Pourquoi
- Permet de retrouver des documents même si les mots ne matchent pas exactement
    - Exemple : "assurance vie" ≈ "contrat épargne long terme"
- Base du RAG → compréhension sémantique

### Source
- https://redis.io/docs/latest/develop/ai/search-and-query/vectors/

---

## 2. Index HNSW

### Description
Choix de l’algorithme **HNSW (Hierarchical Navigable Small World)** pour indexer les vecteurs.

### Détails techniques
```sql
VECTOR HNSW
TYPE FLOAT32
DIM 384
DISTANCE_METRIC COSINE
M 16
EF_CONSTRUCTION 200
```

### Explications techniques
- Structure en graphe multi-niveaux
- Chaque vecteur est connecté à ses voisins proches
- Recherche = navigation dans le graphe (pas scan complet)

### Pourquoi
- Complexité quasi logarithmique
- Très rapide comparé à un scan brut
- Supporte très bien les gros volumes (>1M vecteurs)

### Source
- https://redis.io/en/blog/vector-indexes-in-redis/
- https://redis.io/docs/latest/develop/ai/search-and-query/vectors/

---

## 3. Paramétrage HNSW

### Détails techniques
- M = 16
    - Nombre de connexions par nœud
    - ↑ M :
        - ↑ précision
        - ↑ mémoire
        - ↑ coût de construction
- EF_CONSTRUCTION = 200
    - Taille de la liste de candidats pendant la construction
    - ↑ EF_CONSTRUCTION : 
        - meilleur graphe 
        - meilleur recall
        - indexation plus lente
- EF_RUNTIME = 100
    - Nombre de candidats explorés à la requête
    - Paramètre dynamique :
        ```python
        "PARAMS", "4", "vec", vec, "EF_RUNTIME", "100"
        ```
    - ↑ EF_RUNTIME : 
        - ↑ précision
        - ↑ latence

### Pourquoi
Permet de contrôler le trade-off :
- Latence vs précision
- Mémoire vs qualité

### Source
- https://redis.io/docs/latest/develop/ai/search-and-query/vectors/

---

## 4. Hybrid Search (Vector + Metadata)

### Description
Combinaison de :
- recherche vectorielle (approximation sémantique)
- filtres structurés (exact match)

### Détails techniques
```sql
@contract_types:{assurance_vie}=>[KNN 10 @embedding $vec AS score]
```
- @contract_types:{assurance_vie} → filtre exact
- KNN → tri par similarité sémantique

### Pourquoi
- Vector seul :
    - trop de bruit
    - résultats hors sujet
- Filtre seul :
    - trop strict
    - manque de flexibilité
- Hybrid :
    - précision métier + pertinence sémantique

### Source
- https://redis.io/docs/latest/develop/ai/search-and-query/vectors/

---

## 5. Utilisation des TAG (metadata)

### Description
Utilisation de champs TAG pour indexer des données structurées.

### Détails techniques
```
contract_types TAG
segment TAG
```

#### Stockage
```
contract_types TAG
segment TAG
```

#### Requête
```sql
@contract_types:{assurance_vie}
```

### Pros
- Index inversé très performant
- Matching exact (pas d’ambiguïté)
- Pas dépendant du texte libre

### Cons
- Pas de recherche partielle
- Sensible au format (ex: underscores)

---

## 6. Limite du KNN (Top-K)

### Description
Redis retourne uniquement les K meilleurs voisins.

### Détails techniques
```sql
KNN 10 / 50 / 100
```

#### Impact sur RAG
- Contexte incomplet
- Certaines réponses manquantes

#### Trade-off
| K | Avantage | Inconvénient |
|-------|-----|------------|
| 10 | rapide | peu de contexte |
| 50 | bon compromis | latence |
| 100+ | meilleur recall | coûteux |

### Pros
- Contexte limité pour le RAG
- Trade-off :
    - petit K → rapide mais incomplet
    - grand K → plus complet mais plus lent

### Cons
- Tu ne récupères jamais toute la base
- Seulement un échantillon pertinent

### Source
- https://redis.io/docs/latest/develop/ai/search-and-query/vectors/

---

## 7. Pipeline Redis (ingest)

### Description
Batch des écritures Redis via pipeline.

### Détails techniques
```python
pipe = r.pipeline(transaction=False)

pipe.hset(...)
pipe.hset(...)

pipe.execute()
```

### Pourquoi
- 1 seul aller-retour réseau pour N opérations
- Ingestion plus rapide

---

## 8. Batch Embedding

### Description
Encodage des textes en batch côté modèle.

### Détails techniques
```python
model.encode(texts, batch_size=128)
```

### Pourquoi
- Vectorisation GPU/CPU
- Réduction overhead Python
- Accélération des performances

---

## 9. Structuration des données

### Description
Format standardisé pour améliorer embeddings et extraction.

### Exemple
```
Client X, age, ville, segment.
Contrat TYPE=xxx montant=xxx statut=xxx
```

### Pros
- Meilleure qualité d’embedding
- Facilite l’extraction côté LLM et réduit les hallucinations

---

## 10. Architecture RAG

### Description
Pipeline en 3 étapes :
- Retrieval (Redis)
- Construction du contexte
- Génération (LLM)

### Détails techniques
```python
results = search(query)
context = build_context(results)
response = ask_llm(context + query)
```

### Pros
- Le LLM ne connaît pas les données
- On injecte les données dynamiquement
- Réduction hallucinations

### Source
- https://redis.io/en/blog/vector-indexes-in-redis/ 

---

## 11. Hybrid Routing (logique métier)

### Description
Séparation entre :
- requêtes déterministes → Redis direct
- requêtes ouvertes → RAG

### Détails techniques
```python
if "quels clients" in query:
    return get_clients_by_contract_type()
```

### Pros
- Réponses exactes sur données critiques
- Évite l’usage inutile du LLM

---

## 12. Gestion de la volumétrie

### Description

Optimisation mémoire et scalabilité.

### Détails techniques

#### Embedding

- ~384 dimensions par vecteur
- FLOAT32 = 4 bytes
-> ~1.5KB / doc

#### Index

- HNSW en mémoire
- Overhead graph

#### Exemple réel

10k docs :
- ~18 MB vecteurs
- ~6 MB index

### Cons
- RAM limitée
- croissance linéaire

### Troubleshooting
- Réduction dimension (e.g. 384 → 256)
- Quantization (FLOAT16 / INT8)
- Sharding Redis
- External vector DB si scale extrême