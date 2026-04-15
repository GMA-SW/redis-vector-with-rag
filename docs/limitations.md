---
layout: default
title: Limitations et améliorations
---

## Limites observées

### Recherche par nom inefficace
- Le nom est dans content → dépend du vector search
- Solution : ajouter champ name TEXT

### Contexte limité
- KNN limite le nombre de documents
- Problème pour requêtes globales

### Mélange de cas d'usage
- Certaines requêtes ≠ RAG
- Ex : "liste complète"

---

## Améliorations possibles

### Index supplémentaires
```sql
name TEXT
client_id TAG
```

### Multi-retrieval
- plusieurs requêtes KNN
- fusion des résultats

### Reranking
- cross-encoder
- tri plus précis

### Chunking
- découper documents
- améliorer recall