# Evidence-Grounded-RAG

A research-oriented Retrieval-Augmented Generation system focused on evidence retrieval, grounded answers, citations, and measurable evaluation.

## Why this project exists

A useful RAG system is more than sending retrieved text to an LLM. Its quality depends on the entire evidence pipeline: document parsing, chunking, embeddings, retrieval, ranking, context construction, generation, and evaluation.

This project will make those stages explicit and testable.

## Current status

The repository is at the foundation stage. Implementation will be added incrementally according to [ROADMAP.md](./ROADMAP.md).

## Intended pipeline

```
Documents
   ↓
Parsing
   ↓
Structure-aware Chunking
   ↓
Embeddings
   ↓
Vector Index
   ↓
Hybrid Retrieval
   ↓
Reranking
   ↓
Relevant Evidence
   ↓
Context Construction
   ↓
LLM
   ↓
Grounded Answer + Citations
   ↓
Evaluation
```

## Project direction

The goal is to build a system that can answer questions from a controlled knowledge base while showing:

- what evidence was retrieved;
- why that evidence was selected;
- where an answer came from;
- when the available evidence is insufficient;
- and how retrieval and answer quality are measured.

See [ROADMAP.md](./ROADMAP.md) for the planned development path.
