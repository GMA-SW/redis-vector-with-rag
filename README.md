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

**Note** : Les commandes qui vont suivre sont à exécuter dans le dossier **poc-rag-cluster**. Il faudra parfois se déplacer dans les dossiers si nécessaires.

### Troubleshooting

Afin d'accéder aux logs des pods vous pouvez faire la commande suivante en ayant au préalable récupérer le nom du pod cible :
```bash
sudo kubectl logs nom-pod
```

### Redis Stack
#### Deployment
```bash
sudo kubectl apply -f redis-stack.yaml
```
#### Check
```bash
sudo kubectl get svc
sudo kubectl get pods
```

On doit trouver un service **redis-stack** et les pods associés en running.

### Agent IA
#### Deployment
```bash
sudo kubectl apply -f ai/ollama-mistral.yaml
```
#### Check
```bash
sudo kubectl get svc
sudo kubectl get pods
```

On doit trouver un service **ollama** et le pods **ollama** en running ainsi que le job **ollama-pull-mistral** qui devra finir par être completed (il faut attendre).

### RAG API
#### Image Docker
```bash
sudo docker build -t redis-rag-api .
sudo docker save redis-rag-api | sudo k3s ctr images import -
```

**Note** : J'utilise K3S mais c'est adaptable.

#### Deployment
```bash
sudo kubectl apply -f api/rag-api.yaml
```
#### Check
```bash
sudo kubectl get svc
sudo kubectl get pods
```

On doit trouver un service **redis-rag-api** et le pods **redis-rag-api** en running.

### RAG UI
#### Image Docker
```bash
sudo docker build -t redis-rag-ui .
sudo docker save redis-rag-ui | sudo k3s ctr images import -
```
#### Deployment
```bash
sudo kubectl apply -f ui/rag-ui.yaml
```
#### Check
```bash
sudo kubectl get svc
sudo kubectl get pods
```

On doit trouver un service redis-rag-ui et le pods redis-rag-ui en running.

### Port-forwarding
Les commandes suivantes ont pour objectif de rendre visibles les pods en dehors du cluster. (NodePort)
#### Redis Stack
```bash
sudo kubectl port-forward svc/redis-stack 6379:6379
```

#### RAG API
```bash
sudo kubectl port-forward svc/redis-rag-api 8001:8001
```

#### RAG UI
```bash
sudo kubectl port-forward svc/redis-rag-ui 8501:8501
```

#### Agent IA
```bash
sudo kubectl port-forward svc/ollama 11434:11434
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

## Redis

### Accès à redis-cli
```bash
sudo kubectl get pods
```

On récupère le nom du pod redis-stack puis on va ouvrir le shell associé à ce pod :

```bash
sudo kubectl exec -it redis-stack-xxx -- sh
```

Puis une fois que vous êtes dans votre pod :
```bash
redis-cli
```

Vous aurez alors accès à la console du client redis afin d'exécuter des requêtes et commandes redis.

### Redis UI

Accéder à l'interface de Redis à l'adresse localhost:8001


## 4. Génération des données

Générer les datasets clients et contrats :

python data/generate_data.py

Fichiers générés :

- clients.jsonl
- contracts.jsonl

---

## 5. Ingestion dans Redis

Lancer l’ingestion :

python ingest/ingest.py

Vérifications :

Nombre de documents :

redis-cli KEYS "doc:*" | wc -l

Statut de l’index :

FT.INFO idx:docs

---

## 6. Recherche de données

### Recherche vectorielle

Permet de rechercher des informations similaires :

python search/search.py

---

### Recherche avec filtre

Exemple :

FT.SEARCH idx:docs "@contract_types:{assurance_vie}"

---

## 7. Utilisation du RAG

Lancer le script :

python rag/rag.py

---

### Exemples de requêtes

Requête simple :

Donne moi les informations sur un client

Requête avec filtre :

Quels clients ont un contrat d'assurance vie ?

Requête analytique :

Quels contrats sont associés à une assurance vie ?

---

## 8. Fonctionnement des requêtes

Trois types de traitement :

1. Requête structurée  
→ directement traitée par Redis  

2. Requête sémantique  
→ vector search + LLM  

3. Requête analytique  
→ filtre Redis + analyse LLM  

---

## 9. Nettoyage de Redis

Vider la base :

redis-cli FLUSHALL

---

## 10. Dépannage

### Aucun résultat

- Vérifier que les données sont ingérées
- Vérifier l’index Redis

### Erreur de connexion

- Vérifier les ports (8000, 8501, 6379)
- Vérifier les pods Kubernetes

### LLM ne répond pas

- Vérifier Ollama
- Vérifier que le modèle mistral est lancé

---

## 11. Bonnes pratiques

- Utiliser les filtres pour améliorer les résultats
- Augmenter K pour enrichir le contexte
- Limiter le volume pour les tests

