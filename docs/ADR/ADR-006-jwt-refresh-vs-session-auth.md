# ADR-006: JWT with refresh tokens vs session-based auth

## Context
The system needs authenticated access for government users, reviewers, and administrators, with the possibility of API access from multiple clients. Sessions must support secure renewal without forcing frequent reauthentication.

## Options Considered
- JWT access tokens with refresh tokens.
- Traditional server-side sessions.
- Stateless JWT without refresh tokens.

## Chosen Approach
Use JWT access tokens with refresh tokens, combined with strict revocation and rotation policies.

## Consequences
- The system can support browser and API clients consistently.
- Access tokens can be short-lived while refresh tokens reduce user friction.
- Token rotation and revocation handling must be implemented carefully to preserve security.
- The authentication layer becomes more complex than a basic session cookie model.
