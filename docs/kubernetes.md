---
layout: default
title: Cluster K8S
---
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