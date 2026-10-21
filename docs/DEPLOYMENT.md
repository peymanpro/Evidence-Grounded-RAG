# Deployment

## Local

Install the package and run the API with:

```bash
pip install -e ".[dev]"
uvicorn examples.api_server:app --reload
```

The API exposes `GET /health` and `POST /ask`.

## Provider configuration

The OpenAI-compatible adapters use:

- `RAG_API_KEY`
- `RAG_API_BASE_URL` (optional; defaults to OpenAI-compatible `/v1`)
- `RAG_EMBEDDING_MODEL`
- `RAG_LLM_MODEL`

The provider layer is deliberately HTTP-based so compatible hosted or self-hosted services can be used without coupling the core to one SDK.

## Local Docker Compose

The repository includes a non-root Docker image and a Compose service for reproducible local startup.

```bash
docker compose up --build --detach
docker compose ps
curl http://localhost:8000/health
docker compose logs --follow api
docker compose down
```

Set `RAG_PORT` to change the host port; the container listens on port `8000`. The image health check probes `/health`.

This is currently a packaging and startup milestone, not a production deployment. The API does not yet load a knowledge corpus or configure the RAG pipeline automatically, so `POST /ask` cannot yet execute end-to-end RAG from the container. Complete startup configuration, corpus ingestion, persistence, security controls, and real-corpus evaluation before public exposure.

## Production boundary

Before public deployment, configure a persistent database, authentication, rate limiting, secret management, monitoring, backups, and an evaluated knowledge corpus.
