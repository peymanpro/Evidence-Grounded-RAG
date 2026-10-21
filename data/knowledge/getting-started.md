# Evidence-Grounded RAG — Demo Knowledge Base

This directory contains Markdown documents that the API can ingest when a compatible
embedding and chat-completion provider is configured.

The RAG pipeline splits documents into chunks, embeds those chunks, combines lexical
and semantic retrieval, reranks candidate passages, and gives selected evidence to the
answer generator. Generated answers should cite the supplied evidence identifiers.

The local hashing embedder is a deterministic development baseline. It is not a
production semantic embedding model. A real provider must be configured using the
environment variables documented in the repository README.

This small file is only a sample corpus to verify ingestion and startup wiring.
Replace or supplement it with your own relevant Markdown knowledge sources.
