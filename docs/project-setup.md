---
layout: default
title: Project setup
---

## Génération des données

Générer les datasets clients et contrats :

```bash
python data/generate_data.py
```

Fichiers générés :

- clients.jsonl
- contracts.jsonl

---

## Ingestion dans Redis

Lancer l’ingestion :

```bash
python ingest/ingest.py
```
Vérifications :

Nombre de documents :

```bash
redis-cli KEYS "doc:*" | wc -l
```
Statut de l’index :

```bash
FT.INFO idx:docs
```

---

## Recherche de données

### Recherche vectorielle

Permet de rechercher des informations similaires :
```bash
python search/search.py
```

---

### Recherche avec filtre

Exemple :
```bash
FT.SEARCH idx:docs "@contract_types:{assurance_vie}"
```
---

## Utilisation du RAG

Lancer le script :
```bash
python rag/rag.py
```

---

### Exemples de requêtes

Requête simple :

- Donne moi les informations sur un client

Requête avec filtre :

- Quels clients ont un contrat d'assurance vie ?

Requête analytique :

- Quels contrats sont associés à une assurance vie ?

---

## Fonctionnement des requêtes

Trois types de traitement :

1. Requête structurée  
→ directement traitée par Redis  

2. Requête sémantique  
→ vector search + LLM  

3. Requête analytique  
→ filtre Redis + analyse LLM  

---

## Nettoyage de Redis

Vider la base :
```bash
redis-cli FLUSHALL
```

---

## Troubleshooting

### Aucun résultat

- Vérifier que les données sont ingérées
- Vérifier l’index Redis

### Erreur de connexion

- Vérifier les ports (8000, 8501, 6379)
- Vérifier les pods Kubernetes

### LLM ne répond pas

- Vérifier Ollama
- Vérifier que le modèle mistral est lancé