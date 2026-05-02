# Frontend Tests

This folder contains frontend test suites, MSW mocks, and testing utilities for the admin and audit UI.

Recommended setup:

1. Add a frontend package manifest if one does not exist.
2. Install test dependencies such as `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `msw`, and `whatwg-fetch`.
3. Use `frontend/tests/setup.ts` as the global test setup file.

Sample test commands:

- `npx vitest run`
- `npx vitest watch`
