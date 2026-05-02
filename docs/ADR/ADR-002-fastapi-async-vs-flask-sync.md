# ADR-002: FastAPI + async vs Flask + sync processing

## Context
The platform must ingest PDFs, run extraction pipelines, validate provenance, serve review UIs, and handle long-running background tasks. Request handling needs to remain responsive while workers process CPU- and I/O-heavy jobs.

## Options Considered
- Flask with synchronous request handling.
- FastAPI with asynchronous endpoints and async-aware dependencies.
- Flask with additional worker abstractions to simulate async behavior.

## Chosen Approach
Use FastAPI with async endpoints for I/O-bound operations, while delegating long-running work to background workers.

## Consequences
- The API can handle concurrent requests more efficiently for upload, fetch, and review workflows.
- Modern typing and request validation align well with the system's need for explicit contracts.
- Async does not remove the need for workers, so task orchestration remains a separate concern.
- Developers must be careful to avoid mixing blocking calls into async paths.
