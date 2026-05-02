# Mission Statement

This system exists to transform court judgment PDFs into verified, actionable compliance plans that support government decision-making while preserving legal accuracy, human authority, and complete auditability. It is designed to extract information, organize obligations, and assist review, but never to replace human judgment or create operational action from unverified machine output.

## Core Principles

1. **Human authority is final**
   - Human review and approval always supersede AI extraction.
   - The system may recommend, draft, or highlight, but it cannot authorize action.
   - Any conflict between AI output and human determination is resolved in favor of the human verifier.

2. **Source traceability is mandatory**
   - Every extracted field must trace back directly to the source PDF.
   - Each field must include a verifiable reference to the exact page, section, or text span used for extraction.
   - If a field cannot be traced to source, it must not be treated as valid.

3. **Verification before action**
   - No action plan item may exist unless the underlying extraction has been independently verified.
   - Verified extraction is a prerequisite for creating, editing, or activating any compliance task.
   - Unverified content may be displayed for review only and must remain non-actionable.

4. **Fail closed**
   - When confidence is insufficient, source evidence is missing, validation fails, or traceability is incomplete, the system must stop rather than proceed.
   - The system must never assume completion, never infer authorization, and never convert uncertainty into action.
   - Any ambiguous, conflicting, or incomplete record remains blocked until a human resolves it.

5. **Immutable auditability**
   - Every extraction, verification step, human decision, and action status change must be recorded in a complete audit trail.
   - The audit trail must be immutable, append-only, and preserved without silent modification or deletion.
   - The system must be able to explain what was extracted, from where, by whom it was verified, and when it became actionable.

## Non-Negotiable Constraints

- The system must never present AI output as authoritative without human verification.
- The system must never create an actionable record from an unverified extraction.
- The system must never synthesize a compliance obligation that is not supported by the source PDF.
- The system must never hide missing provenance, validation failures, or human overrides.
- The system must never allow an action plan item to bypass traceability requirements.
- The system must never delete, rewrite, or obscure audit evidence.
- The system must never default to permissive behavior when verification is incomplete.
- The system must always preserve the chain from PDF source to extracted field to verified record to action plan.

## Operational Rule

If a judgment, field, or proposed action cannot be verified against the source PDF and confirmed by a human reviewer, it must remain non-actionable and the system must fail closed.
