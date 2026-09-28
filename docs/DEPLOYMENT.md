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

## Production boundary

Before public deployment, configure a persistent database, authentication, rate limiting, secret management, monitoring, backups, and an evaluated knowledge corpus.
