# Redis RAG POC

Ce projet démontre la mise en place d’un système RAG (Retrieval-Augmented Generation)
à grande échelle basé sur Redis Stack.

## Objectifs

- Gérer 1M+ clients et contrats
- Indexation vectorielle avec Redis
- Recherche hybride (vector + filtres)
- Pipeline RAG avec LLM (Ollama / Mistral)
- Déploiement Kubernetes

## Architecture

Sources de données actuelles:
- Json Clients
- Json Contrats

Pipeline actuelle:
JSON → Ingest → Redis (Vector DB) → Search → RAG → LLM

Sources de données cibles:
- API Clients
- API Contrats

Pipeline cible:
API → Ingest → Redis (Vector DB) → Search → RAG → LLM

Technologies :
- Redis Stack (Vector Search)
- SentenceTransformers
- Ollama (Mistral)
- Kubernetes

## ⚙️ Kubernetes Setup


```

## Python

### Installation
```bash
sudo apt install python3-venv -y
```
### Création d'un environnement
```bash
python3 -m venv venv
```
### Activation de l'environnement
```bash
source venv/bin/activate
```

Vous devez avoir : (venv) user@machine:~

### Désactivation
```bash
deactivate
```





---

## 11. Bonnes pratiques

- Utiliser les filtres pour améliorer les résultats
- Augmenter K pour enrichir le contexte
- Limiter le volume pour les tests

