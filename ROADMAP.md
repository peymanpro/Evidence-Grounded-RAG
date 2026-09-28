# Evidence-Grounded-RAG

A research-oriented RAG system focused on retrieving reliable evidence, grounding generated answers in that evidence, and measuring retrieval and answer quality.

## Project goal

Build a RAG system that goes beyond "chat with a PDF".

The system should make the full path observable and testable:

Documents → Parsing → Structure-aware Chunking → Embeddings → Indexing → Hybrid Retrieval → Reranking → Context Construction → LLM → Grounded Answer + Citations → Evaluation

The project is intended as practical evidence of AI engineering capability, while keeping the engineering and research decisions explicit.

## Roadmap

### Phase 0 — Foundation
- [x] Create the private repository
- [ ] Define project structure
- [x] Add initial documentation
- [ ] Define technology choices and boundaries
- [ ] Establish local development and test workflow

### Phase 1 — Ingestion
- [ ] Define a document model
- [ ] Support an initial document format
- [ ] Extract text and structural metadata
- [ ] Implement structure-aware chunking
- [ ] Preserve source, section, and document metadata
- [ ] Add ingestion tests

### Phase 2 — Embeddings and Index
- [ ] Define embedding provider boundary
- [ ] Generate embeddings for chunks
- [ ] Store chunks and metadata
- [ ] Add vector search
- [ ] Make indexing repeatable and idempotent
- [ ] Test indexing behavior

### Phase 3 — Retrieval
- [ ] Implement semantic retrieval
- [ ] Add keyword retrieval
- [ ] Combine retrieval signals
- [ ] Introduce reranking
- [ ] Expose retrieval scores and evidence
- [ ] Build a small retrieval benchmark

### Phase 4 — Grounded Generation
- [ ] Construct context from retrieved evidence
- [ ] Generate answers from retrieved evidence
- [ ] Attach source citations to claims
- [ ] Define behavior when evidence is insufficient
- [ ] Add tests for grounding and citation behavior

### Phase 5 — Evaluation
- [ ] Create a representative question set
- [ ] Measure retrieval quality separately from generation quality
- [ ] Compare retrieval strategies
- [ ] Measure citation/evidence coverage
- [ ] Track latency and cost where applicable
- [ ] Document failure cases and limitations

### Phase 6 — Application
- [ ] Expose the system through a clean API
- [ ] Add a minimal user interface
- [ ] Show retrieved evidence alongside answers
- [ ] Add observability for the retrieval pipeline
- [ ] Add end-to-end tests

### Phase 7 — Hardening
- [ ] Review security and input boundaries
- [ ] Review prompt-injection risks in retrieved documents
- [ ] Improve error handling
- [ ] Improve reproducibility
- [ ] Document deployment architecture
- [ ] Prepare a production-oriented example

## Non-goals

- Building a generic chatbot without measurable retrieval quality
- Hiding retrieval decisions behind a single framework abstraction
- Claiming production readiness before the relevant evidence exists
- Optimizing for the number of technologies rather than system quality

## Guiding principles

1. Evidence before generation.
2. Retrieval quality is measured independently from answer quality.
3. Every major architectural choice should have a reason.
4. Failure cases are part of the project, not something to hide.
5. Start small, keep each stage runnable, and expand only when the previous stage is understood.
6. Prefer clear engineering boundaries over unnecessary abstraction.
