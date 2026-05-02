# Shared

This folder contains shared contracts, constants, types, and schemas used by multiple packages (backend, frontend, and worker).

Purpose:
- Centralize DTOs, JSON schemas, and TypeScript/Python types to keep services consistent.

Usage:
- Import from `shared/schemas` or `shared/types` in service code. Keep changes backwards-compatible or coordinate deploys.

Testing:
- Shared schema tests and contract checks should be run as part of CI to prevent breaking consumers.

See also:
- [ADR/ADR-001-monorepo-shared-types.md](docs/ADR/ADR-001-monorepo-shared-types.md)
