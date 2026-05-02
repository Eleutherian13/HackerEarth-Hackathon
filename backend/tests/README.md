# Backend Tests

This folder contains automated tests for the backend service.

New test infrastructure includes:

- `tests/factories.py` for reusable domain object fixtures.
- `tests/utils.py` for fake SQLAlchemy session/query helpers.
- `tests/unit/test_audit_core.py` for audit helper coverage.
- `tests/unit/test_admin_endpoints.py` for admin endpoint logic.
- `tests/integration/test_admin_api.py` for FastAPI admin route integration.
