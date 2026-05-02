# ADR-008: Storage strategy: local vs S3-compatible vs database BLOB

## Context
The system stores original PDFs, derived previews, extraction artifacts, and audit evidence. These artifacts must be durable, retrievable, and suitable for scale. Storage also needs to support retention policies and environment parity across development and production.

## Options Considered
- Local filesystem storage.
- S3-compatible object storage.
- Database BLOB storage.

## Chosen Approach
Use S3-compatible object storage for documents and derived artifacts, while keeping metadata and audit references in PostgreSQL.

## Consequences
- The system can scale storage independently from application and database tiers.
- Object storage is better suited for large binary PDFs than database BLOBs.
- Local development can mirror production behavior with an S3-compatible endpoint.
- Access control and lifecycle policies must be enforced at the storage layer.
