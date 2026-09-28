# Evidence-Grounded-RAG

A research-oriented RAG system focused on retrieving reliable evidence, grounding generated answers in that evidence, and measuring retrieval and answer quality.

## Project goal

Build a RAG system that goes beyond "chat with a PDF".

Documents → Parsing → Structure-aware Chunking → Embeddings → Indexing → Hybrid Retrieval → Reranking → Context Construction → LLM → Grounded Answer + Citations → Evaluation

## Current status

**Foundation + initial ingestion are implemented.** The repository is intentionally growing in small, testable stages.

## Roadmap

### Phase 0 — Foundation
- [x] Private repository
- [x] Project structure
- [x] Initial documentation
- [x] Initial technology boundary
- [ ] CI and broader local workflow

### Phase 1 — Ingestion
- [x] Document model
- [x] Initial Markdown source
- [x] Basic structural metadata
- [x] Structure-aware paragraph chunking
- [x] Source/document metadata preservation
- [x] Ingestion and chunking tests
- [ ] Heading/section metadata
- [ ] Additional source formats

### Phase 2 — Embeddings and Index
- [ ] Embedding provider boundary
- [ ] Chunk embeddings
- [ ] Persistent chunk/metadata store
- [ ] Vector search
- [ ] Repeatable, idempotent indexing
- [ ] Indexing tests

### Phase 3 — Retrieval
- [ ] Semantic retrieval
- [ ] Keyword retrieval
- [ ] Hybrid retrieval
- [ ] Reranking
- [ ] Retrieval evidence and scores
- [ ] Retrieval benchmark

### Phase 4 — Grounded Generation
- [ ] Evidence-based context construction
- [ ] LLM generation
- [ ] Source citations
- [ ] Insufficient-evidence behavior
- [ ] Grounding/citation tests

### Phase 5 — Evaluation
- [ ] Representative question set
- [ ] Retrieval metrics independent from generation
- [ ] Strategy comparisons
- [ ] Citation/evidence coverage
- [ ] Latency/cost tracking
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
