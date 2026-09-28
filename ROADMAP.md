# Evidence-Grounded-RAG

A research-oriented RAG system focused on retrieving reliable evidence, grounding generated answers in that evidence, and measuring retrieval and answer quality.

## Current status

**Core retrieval foundation is implemented.**

The repository now has ingestion, chunking, lexical retrieval, an embedding boundary with a deterministic local baseline, vector search, hybrid rank fusion, evidence/context construction, retrieval metrics, grounded-generation boundaries, tests, and CI.

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
- [x] Vector search boundary
- [ ] Production embedding provider
- [ ] Persistent vector database
- [ ] Repeatable, idempotent indexing

### Phase 3 — Retrieval
- [x] Lexical retrieval baseline
- [x] Semantic retrieval baseline
- [x] Hybrid retrieval
- [ ] Production-grade reranking
- [x] Retrieval evidence and scores
- [x] Initial evaluation metrics
- [ ] Versioned retrieval benchmark

### Phase 4 — Grounded Generation
- [x] Evidence selection
- [x] Citation-ready context
- [x] Grounded prompt boundary
- [ ] Production LLM provider
- [ ] Citation verification
- [ ] Insufficient-evidence / abstention policy
- [ ] Grounding evaluation

### Phase 5 — Evaluation
- [x] Retrieval metric implementation
- [ ] Representative benchmark dataset
- [ ] Retrieval strategy comparison
- [ ] Citation/evidence coverage metrics
- [ ] End-to-end answer evaluation
- [ ] Latency and cost tracking
- [ ] Failure-case analysis

### Phase 6 — Application
- [ ] API
- [ ] Minimal UI
- [ ] Evidence display
- [ ] Pipeline observability
- [ ] End-to-end tests

### Phase 7 — Hardening
- [ ] Security and input boundaries
- [ ] Prompt-injection review
- [ ] Error handling
- [ ] Reproducibility
- [ ] Deployment documentation
- [ ] Production-oriented example

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
