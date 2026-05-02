# ADR-010: LangChain for orchestration vs custom pipeline with Pydantic models

## Context
The system needs deterministic extraction, provenance tracking, human verification gates, and audit-grade explainability. The workflow is compliance-sensitive, so every stage must be explicit and testable.

## Options Considered
- LangChain for orchestration.
- A custom pipeline built around Pydantic models and explicit workflow steps.
- A hybrid abstraction with LangChain only for selected components.

## Chosen Approach
Use a custom pipeline with Pydantic models, explicit control flow, and narrow integration points where needed.

## Consequences
- The workflow is easier to reason about and audit because each step is explicit.
- Validation, provenance, and state transitions can be enforced directly in code.
- The system avoids framework-driven indirection that could obscure compliance logic.
- Development may take more effort than adopting a higher-level orchestration framework, but control and clarity are improved.
