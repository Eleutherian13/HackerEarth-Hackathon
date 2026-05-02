# ADR-009: Server-side highlight rendering vs client-side coordinate mapping

## Context
Reviewers need to see extracted text highlighted on the source PDF so they can verify provenance quickly. The system must align highlights with the underlying PDF content and preserve reproducibility in audits.

## Options Considered
- Server-side highlight rendering into precomputed images or overlays.
- Client-side coordinate mapping against the rendered PDF pages.
- A mixed approach that rasterizes highlights before delivery.

## Chosen Approach
Use client-side coordinate mapping for rendered overlays, with server-generated coordinate data derived from the source PDF.

## Consequences
- The UI remains interactive and can adapt to zoom and page scaling.
- Highlight logic stays tied to source coordinates instead of baked images.
- The backend must provide precise coordinate metadata for each verified extraction.
- QA is needed to ensure coordinate accuracy across PDFs with different layouts and encodings.
