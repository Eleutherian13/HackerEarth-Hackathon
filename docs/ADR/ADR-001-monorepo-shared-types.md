# ADR-001: Monorepo structure with shared types

## Context
The system spans PDF ingestion, extraction, verification, workflow orchestration, and audit reporting. These components exchange tightly coupled records such as extracted fields, provenance metadata, verification state, and action-plan items. Schema drift between services would create correctness risk and slow delivery.

## Options Considered
- Separate repositories for each service.
- Monorepo with shared types and shared validation models.
- Monorepo without shared contracts, with each service redefining its own payloads.

## Chosen Approach
Use a monorepo with shared types and shared validation models for all core domain objects.

## Consequences
- Contract changes are easier to coordinate across services.
- Shared models reduce duplication and lower the chance of mismatched field names or validation rules.
- The repository becomes larger and requires discipline around boundaries, ownership, and dependency direction.
- Build and test tooling must support selective execution to keep developer workflows efficient.
