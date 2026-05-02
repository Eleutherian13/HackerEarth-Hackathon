# Architecture Decision Records

This directory documents the major architecture decisions for the court judgment compliance system.

## Index

- [ADR-001: Monorepo structure with shared types](ADR-001-monorepo-shared-types.md)
- [ADR-002: FastAPI + async processing](ADR-002-fastapi-async-vs-flask-sync.md)
- [ADR-003: PostgreSQL with JSONB for extractions](ADR-003-postgresql-jsonb-vs-document-store.md)
- [ADR-004: Redis + Celery for background work](ADR-004-redis-celery-vs-in-memory-queues.md)
- [ADR-005: PDF.js for preview](ADR-005-pdfjs-preview-vs-server-rendering.md)
- [ADR-006: JWT with refresh tokens](ADR-006-jwt-refresh-vs-session-auth.md)
- [ADR-007: Confidence threshold for review flagging](ADR-007-confidence-threshold.md)
- [ADR-008: S3-compatible object storage](ADR-008-storage-local-vs-s3-vs-blob.md)
- [ADR-009: Server-side highlight rendering](ADR-009-highlight-rendering-strategy.md)
- [ADR-010: Custom pipeline with Pydantic models](ADR-010-custom-pipeline-vs-langchain.md)
