# Evidence-Grounded-RAG

A research-oriented RAG system focused on retrieving reliable evidence, grounding generated answers in that evidence, and measuring retrieval and answer quality.

## Current status

**Portfolio-ready RAG MVP is implemented.**

The system now covers the full architectural path from ingestion and hybrid retrieval through reranking, evidence selection, citation verification, grounded generation adapters, evaluation, persistence, and an HTTP API. Production deployment still depends on choosing and operating external embedding/LLM infrastructure and an evaluated real knowledge corpus.

## Roadmap

### Phase 0 — Foundation
- [x] Private repository
- [x] Project structure
- [x] Initial documentation
- [x] Technology boundaries
- [x] Automated tests and CI

### Phase 1 — Ingestion
- [x] Document model
- [x] Markdown source
- [x] Basic structural metadata
- [x] Structure-aware paragraph chunking
- [x] Source/document metadata preservation
- [x] Ingestion and chunking tests
- [ ] Heading/section metadata
- [ ] Additional source formats

### Phase 2 — Embeddings and Index
- [x] Embedding provider boundary
- [x] Deterministic local embedding baseline
- [x] OpenAI-compatible embedding adapter
- [x] Vector search boundary
- [x] Persistent SQLite vector store
- [x] Repeatable upsert semantics
- [ ] Managed/vector-database deployment adapter

### Phase 3 — Retrieval
- [x] Lexical retrieval baseline
- [x] Semantic retrieval baseline
- [x] Hybrid retrieval
- [x] Second-stage reranking boundary and deterministic implementation
- [x] Retrieval evidence and scores
- [x] Retrieval evaluation metrics
- [x] Benchmark dataset format
- [ ] Cross-encoder reranker

### Phase 4 — Grounded Generation
- [x] Evidence selection
- [x] Citation-ready context
- [x] Grounded prompt boundary
- [x] OpenAI-compatible LLM adapter
- [x] Citation verification
- [x] Explicit insufficient-evidence path
- [ ] Model-specific grounding benchmark

### Phase 5 — Evaluation
- [x] Recall@k
- [x] Precision@k
- [x] Reciprocal rank
- [x] nDCG@k
- [x] Representative benchmark format
- [ ] Measured benchmark report on a real corpus
- [ ] Latency and cost tracking
- [ ] Failure-case analysis

### Phase 6 — Application
- [x] HTTP API
- [x] Health endpoint
- [x] Ask endpoint with citation metadata
- [x] Minimal runnable server example
- [ ] Browser UI
- [ ] End-to-end production corpus ingestion
- [ ] Pipeline observability

### Phase 7 — Hardening
- [x] Security boundaries documented
- [x] Prompt-injection boundary documented
- [x] Deployment documentation
- [x] Provider configuration through environment variables
- [ ] Authentication and rate limiting
- [ ] Production monitoring and backups
- [ ] Public deployment

## Non-goals

- A generic chatbot without measurable retrieval quality
- Hiding retrieval decisions behind one framework abstraction
- Claiming production readiness without evidence
- Optimizing for technology count

## Guiding principles

1. Evidence before generation.
2. Retrieval quality is measured independently from answer quality.
3. Major architectural choices need explicit reasons.
4. Failure cases are part of the project.
5. Keep every stage runnable.
6. Prefer clear boundaries over unnecessary abstraction.
