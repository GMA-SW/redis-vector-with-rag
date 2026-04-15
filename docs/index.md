---
layout: default
title: Accueil
---

# Proof of Concept for high volumetry with Redis Vector associated to RAG

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

---

Sources de données cibles:
- API Clients
- API Contrats

Pipeline cible:
API → Ingest → Redis (Vector DB) → Search → RAG → LLM

---

Technologies :
- Redis Stack (Vector Search)
- SentenceTransformers
- Ollama (Mistral)
- Kubernetes

---

## Environment setup
- [Cluster K8S](kubernetes.md)
- [Environnement python](python.md)

## Guidelines
- [Redis Vector Database](redis.md)

## Optimizations & Limitations
- [Optimizations & Performance](optimizations.md)
- [Limitations & Améliorations](limitations.md)