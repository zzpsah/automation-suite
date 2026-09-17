# DevOS Document Intelligence

Evidence-first web archive for government/school letters. The browser is the primary interface; Telegram is not part of the core pipeline.

## MVP implemented

- Next.js web dashboard suitable for Vercel.
- Private access guard using an application password and signed HTTP-only session cookie.
- Direct browser-to-Cloudflare R2 uploads through short-lived presigned PUT URLs.
- Original files are stored under `original/YYYY-MM-DD/<uuid>-filename` and are never overwritten by OCR/AI output.
- Supabase metadata/control plane with document, page, relation, automation-job and audit tables.
- Atomic queue claiming with `FOR UPDATE SKIP LOCKED`.
- Full-text search across filename, subject, authority, reference number, description and raw OCR.
- Reusable GovDOC OCR integration: native PDF text is used where present; sparse/scanned pages are rendered and routed through Hindi+English OCR.
- OCR regions, diagnostics, visual-mark evidence and provenance remain derived data; no source text or geometry is fabricated.
- Scheduled GitHub Actions worker processes bounded batches of queued documents.

## Deployment

### Vercel
Set the variables in `.env.example` as Vercel server-side environment variables. Set the project root to `document-intelligence` and build with `npm run build`.

### Supabase
Run these migrations in order:

1. `supabase/migrations/001_document_intelligence.sql`
2. `supabase/migrations/002_queue_and_search.sql`

Create an R2 bucket and CORS rule permitting `PUT` from the deployed web-app origin. Never expose the R2 secret or Supabase service-role key to client code.

### GitHub Actions worker
Add repository Actions secrets:

- `DI_SUPABASE_URL`
- `DI_SUPABASE_SERVICE_ROLE_KEY`
- `DI_R2_ACCOUNT_ID`
- `DI_R2_ACCESS_KEY_ID`
- `DI_R2_SECRET_ACCESS_KEY`
- `DI_R2_BUCKET`

The worker runs every 10 minutes and handles up to five queued documents per run. It can also be started manually.

## First real fixture

`transfer order.pdf` supplied during development is a scanned one-page transfer/posting order. The uploaded PDF has no parseable native text, so it is a required regression case for the PDF-image fallback. Its page contains the issuing office, order date/reference, teacher details, current/new posting table, UDISE codes and numbered instructions. The original document remains the evidence source.

## Data model

```text
documents
  ├── document_pages
  ├── document_relations
  ├── automation_jobs
  └── document_audit
```

`documents.extraction_json` stores the versioned GovDOC result. `document_pages.regions` stores backend-derived OCR geometry. `document_audit` records processing events and errors.

## Human-interaction policy

High-confidence extraction can proceed automatically. Low-confidence OCR becomes `review_required`. Portal automation is a separate stage and must stop for OTP, CAPTCHA, security-key or other human authentication. No portal adapter is included in this MVP, so the MVP cannot yet submit forms to a live portal.

## AI enhancement boundary

The MVP deliberately does not silently call a paid/cloud LLM. GovDOC provides deterministic government-document extraction first. An AI enrichment adapter can be added next, receiving OCR + evidence references and writing only derived fields such as summary, topics, entities and relationships. The original document and raw OCR remain immutable evidence.

## Roadmap

1. Add document detail/review page with page image + field-level evidence.
2. Add optional AI enrichment provider interface and structured JSON schema.
3. Add vector/semantic search using pgvector embeddings.
4. Add R2 signed read URLs and secure document viewer.
5. Add portal adapter SDK and Playwright worker with human handoff.
6. Add regression fixtures for Hindi, mixed Hindi-English, tables, multipage and poor scans.
7. Add CI build, worker smoke tests and end-to-end upload/search checks.
