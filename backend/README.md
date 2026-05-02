# Backend

This folder contains the FastAPI application, compliance pipeline, database access, and worker-facing services.

Quickstart:
- Development: see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md#backend)
- Run locally: `uvicorn main:app --reload` from the `backend/` directory

Environment:
- Configure with `.env` or environment variables described in [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#environment)

Testing:
- Unit tests live in `backend/tests/` and run with `pytest` from the repository root.

Useful links:
- API reference: [docs/API.md](docs/API.md)
- Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
