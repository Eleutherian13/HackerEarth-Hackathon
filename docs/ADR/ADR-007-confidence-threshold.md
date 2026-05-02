# ADR-007: Confidence threshold for auto-flagging reviews

## Context
The extraction pipeline produces confidence scores that help determine whether a record is ready for downstream verification or requires human attention. The system must fail closed and protect against overconfident automation.

## Options Considered
- No numeric threshold; rely on ad hoc reviewer judgment.
- A low threshold such as 0.70 to maximize throughput.
- A stricter threshold such as 0.85 to bias toward human verification.

## Chosen Approach
Set the auto-flagging threshold at 0.85. Any extraction below this threshold is automatically flagged for review and is not actionable until verified.

## Consequences
- More records will be routed to human review, improving safety and traceability.
- Throughput may be lower than a permissive threshold, but false confidence is reduced.
- Teams must expect reviewer workload to remain part of normal operations.
- Threshold tuning must be governed and versioned so changes are auditable.
