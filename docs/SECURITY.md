# Security boundaries

The system treats retrieved documents as untrusted input.

- Retrieval content is evidence, not instructions.
- The generation prompt explicitly separates the question from retrieved evidence.
- Citation verification rejects references to evidence identifiers that were not supplied.
- The local Compose API binds to loopback by default rather than exposing its port to other machines.
- The API container uses a read-only root filesystem, a temporary writable `/tmp`, drops Linux capabilities, and enables `no-new-privileges`.
- The PostgreSQL service is not published on a host port by default; persistent database files remain in its named volume.
- A production deployment should isolate secrets in environment variables and never index credentials, tokens, or private keys.
- Documents containing prompt-injection text should be treated as data and evaluated as adversarial cases.
- API deployments should add authentication, rate limiting, request-size limits, structured logging, monitoring, backups, and reviewed network controls before exposure to untrusted clients.

These container settings are a safer local baseline, not a substitute for a complete production security review.
