# ADR-003: PostgreSQL with JSONB for extractions vs document store

## Context
Extractions are semi-structured: each record has stable fields for case metadata, verification status, and provenance, but the set of extracted judgment details can vary by document and jurisdiction. The system also needs transactional integrity, auditability, and queryable relationships between PDFs, extractions, and action plans.

## Options Considered
- PostgreSQL with JSONB for flexible extraction payloads.
- A document database as the primary store.
- A relational schema with no flexible field support.

## Chosen Approach
Use PostgreSQL as the system of record, with JSONB for variable extraction payloads and relational tables for governed entities and audit linkage.

## Consequences
- Core records remain strongly consistent and queryable.
- JSONB provides flexibility without giving up relational constraints for critical workflow objects.
- Reporting and traceability are easier because provenance and status can be joined across tables.
- Schema design must be deliberate so JSONB does not become a dumping ground for governed data.
