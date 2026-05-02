# ADR-005: PDF.js for preview vs server-side rendering

## Context
Users need to inspect the original court judgment PDF while reviewing extracted fields and proposed action plans. The preview layer must be faithful to the source document and responsive enough for interactive review.

## Options Considered
- PDF.js in the client for PDF preview.
- Server-side rendering of pages to images for viewing.
- Hybrid rendering with server-generated previews and client-side interactivity.

## Chosen Approach
Use PDF.js for client-side PDF preview, with the original PDF preserved as the source of truth.

## Consequences
- Reviewers can interact with the actual PDF rather than a flattened image copy.
- The browser handles pagination, zoom, and text layer rendering efficiently.
- Server load is reduced because the app does not need to render every page for every viewer.
- Compatibility testing is needed to ensure stable behavior across browsers and large files.
