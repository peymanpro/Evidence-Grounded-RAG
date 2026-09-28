# Evidence-Grounded-RAG

A research-oriented Retrieval-Augmented Generation system focused on evidence retrieval, grounded answers, citations, and measurable evaluation.

## What is implemented

The current core includes:

- document and chunk models with source metadata;
- Markdown ingestion;
- structure-aware paragraph chunking;
- deterministic lexical retrieval;
- a provider boundary for embeddings;
- a local deterministic embedding baseline;
- in-memory vector search;
- hybrid retrieval with Reciprocal Rank Fusion;
- evidence selection and citation-ready context;
- retrieval evaluation with Recall@k and reciprocal rank;
- an explicit LLM provider boundary;
- automated tests and a small CI workflow.

The local embedding implementation is deliberately a deterministic baseline for offline development and tests. It is **not** presented as a production semantic embedding model.

## Pipeline

```
Documents
   ↓
Parsing
   ↓
Structure-aware Chunking
   ↓
Embedding
   ↓
Vector Index ─────────┐
                      ├→ Hybrid Retrieval → Reranking → Evidence
Keyword Index ────────┘                                  ↓
                                                   Context
                                                      ↓
                                                      LLM
                                                      ↓
                                           Grounded Answer + Citations
                                                      ↓
                                                   Evaluation
```

Reranking and a real embedding/LLM provider remain deliberate next steps rather than hidden assumptions.

## Quick start

```bash
python -m venv .venv
# activate the environment using your platform's command
pip install -e ".[dev]"
pytest
python examples/basic_pipeline.py
```

## Project structure

- `src/evidence_rag/models.py` — core evidence models
- `src/evidence_rag/ingestion.py` — source ingestion
- `src/evidence_rag/chunking.py` — chunking
- `src/evidence_rag/embeddings.py` — embedding boundary and local baseline
- `src/evidence_rag/vector_store.py` — vector storage/search boundary
- `src/evidence_rag/retrieval.py` — lexical retrieval and rank fusion
- `src/evidence_rag/pipeline.py` — retrieval orchestration
- `src/evidence_rag/grounding.py` — evidence selection/context
- `src/evidence_rag/generation.py` — grounded generation boundary
- `src/evidence_rag/evaluation.py` — retrieval evaluation
- `docs/ARCHITECTURE.md` — architectural boundaries
- `docs/EVALUATION.md` — evaluation methodology
- `ROADMAP.md` — development plan

## Design principle

This project is intentionally not "an LLM wrapper".

The important artifact is the measurable evidence pipeline: what was retrieved, why it was retrieved, what evidence was passed to generation, what was cited, and how those decisions are evaluated.

See [ROADMAP.md](./ROADMAP.md) for the development plan.
