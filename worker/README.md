# Worker

This folder contains container-level worker assets and entrypoint scripts used for background processing (Celery, task runners, etc.).

Quickstart:
- See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#workers) for production worker configuration.
- Run locally (example): set environment and run the entrypoint script `entrypoint.sh` in this directory.

Logging & monitoring:
- Workers should emit structured logs compatible with the project's logging system. See [LOGGING_INTEGRATION.md](LOGGING_INTEGRATION.md).

Testing:
- Integration tests for async tasks live in `backend/tests/integration/`.
