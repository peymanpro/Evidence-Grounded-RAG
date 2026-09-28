# Security boundaries

The system treats retrieved documents as untrusted input.

- Retrieval content is evidence, not instructions.
- The generation prompt explicitly separates the question from retrieved evidence.
- Citation verification rejects references to evidence identifiers that were not supplied.
- A production deployment should isolate secrets in environment variables and never index credentials, tokens, or private keys.
- Documents containing prompt-injection text should be treated as data and evaluated as adversarial cases.
- API deployments should add authentication, rate limiting, request-size limits, structured logging, and network controls before exposure to untrusted clients.
