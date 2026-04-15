---
layout: default
title: Redis CLI
---

# Redis CLI

## Accès au container Redis
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

---

## Redis UI

Accéder à l'interface de Redis déployée dans le cluster K8S à l'adresse localhost:8001.