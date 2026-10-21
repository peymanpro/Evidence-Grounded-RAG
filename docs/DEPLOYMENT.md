# Deployment

## Local development

Install the package and run the API with:

```bash
pip install -e ".[dev]"
uvicorn examples.api_server:app --reload
```

The API exposes `GET /health` and `POST /ask`.

## Docker Compose

Prerequisite: Docker Desktop or Docker Engine with the Compose v2 plugin.

Build the image and start the API:

```bash
docker compose build
docker compose up -d
docker compose ps
```

The Compose configuration publishes the API on localhost only. The default URL is `http://127.0.0.1:8000`. On Windows PowerShell, verify the health endpoint with:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
docker compose logs -f api
```

To use a different local port:

```powershell
$env:RAG_PORT = "8080"
docker compose up -d --build
```

Stop the service with:

```bash
docker compose down
```

The image runs as a non-root user. Compose also uses a read-only root filesystem, drops Linux capabilities, enables `no-new-privileges`, and binds the published port to loopback. These controls are a safer local baseline, not a substitute for a complete production security review.

### Current API limitation

This container milestone verifies packaging and API startup. The API does **not yet automatically load a knowledge corpus or configure the production RAG pipeline** at startup. In the current implementation, `/ask` returns the unconfigured-service response until the application wiring is completed in a later phase. Do not present this milestone as a deployed, functional RAG product.

## Provider configuration

The OpenAI-compatible adapters use:

- `RAG_API_KEY`
- `RAG_API_BASE_URL` (optional; defaults to OpenAI-compatible `/v1`)
- `RAG_EMBEDDING_MODEL`
- `RAG_LLM_MODEL`

The provider layer is deliberately HTTP-based so compatible hosted or self-hosted services can be used without coupling the core to one SDK. Provider variables are not wired into API startup yet; avoid placing secrets in source control.

## Production boundary

Before public deployment, configure a real knowledge corpus and provider-backed application startup, a persistent database, authentication, rate limiting, secret management, monitoring, backups, and an evaluated knowledge corpus. The remaining implementation work is tracked in `ROADMAP.md`.
