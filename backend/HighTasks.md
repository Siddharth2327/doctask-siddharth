# Docsnary — Task 1 Completion Checklist

> Reconstructed from the phase breakdown supplied for this work —
> the assistant did not have access to an existing `TASK 1.md` in
> this environment. **If you already have a `TASK 1.md` with other
> content or a different checklist, merge this into it rather than
> replacing it wholesale.**

Status legend: `[x]` done and tested · `[~]` implemented, not yet
live-tested · `[ ]` not started

## Vertical slice (prior work — unchanged this pass)

- [x] FastAPI backend
- [x] PostgreSQL + pgvector
- [x] Redis
- [x] LangGraph workflow
- [x] Checkpoint/resume
- [x] Prompt management
- [x] AI provider abstraction
- [x] Structured extraction
- [x] Evidence persistence
- [x] Chunking
- [x] Embeddings (mock provider)
- [x] pgvector retrieval
- [x] Conflict detection
- [x] Findings
- [x] Human review
- [x] Commit layer
- [x] Async queue
- [x] Incremental updates
- [x] Docsnary MCP server
- [x] 101 passing tests (confirmed by the user against real infra)

## Phase A — Real providers & usage tracking

- [x] OpenAI provider (`app/integrations/ai/openai_provider.py`) — JSON-schema
      constrained chat completions, SDK error mapping, tested (mocked client)
- [x] Anthropic provider (`app/integrations/ai/anthropic_provider.py`) —
      forced tool-use for structured output, tested (mocked client)
- [x] Gemini provider (`app/integrations/ai/gemini.py`) — native JSON
      response mode, tested (mocked client)
- [x] Real embedding provider (`app/integrations/embeddings/openai_embeddings.py`)
      — OpenAI embeddings with configurable `dimensions`; `EMBEDDING_DIMENSIONS`
      moved from a hardcoded constant to a setting; migration + re-embed script
      added for dimension changes
- [x] Token usage tracking — per-call cost estimation (`app/integrations/ai/pricing.py`,
      caught and fixed a prefix-matching bug during testing) wired into the
      existing in-graph usage accumulator; usage now also persisted per-run
      (`runs.input_tokens`/`output_tokens`/`estimated_cost`) and exposed via
      `GET /runs/{run_id}` and the MCP `get_run_status` tool

All Phase A code paths that don't require a live API key were executed
and pass (10 new tests + the full pre-existing DB-independent suite,
zero regressions). The three real providers themselves are untested
against live OpenAI/Anthropic/Gemini APIs — no keys are available in
this environment. See `PROGRESS.md` for the precise verification
level of every item.

## Phase B — Real document processing

- [x] PDF parser (beyond existing pymupdf text extraction — layout/table awareness) — OCR fallback added for scanned pages
- [x] OCR parser (scanned documents) — standalone images (PNG/JPEG/TIFF) + scanned PDF pages, real tesseract, tested end-to-end
- [x] DOCX parser — paragraphs, explicit page-break detection, table extraction
- [x] Page-aware evidence references — evidence location now derived from real parser page structure via the existing retrieval-grounding step, not self-reported by extraction

24 new tests added this pass (16 parser tests + 1 usage-persistence
test + others), all DB-independent ones executed and passing
(including real end-to-end OCR against a real tesseract install). See
`PROGRESS.md` for exact per-item verification level and known
limitations (DOCX auto-pagination is undetectable in principle; OCR
has no image preprocessing yet).

## Phase C — React frontend

- [x] Upload UI — `frontend/src/pages/DocumentsPage.tsx`
- [x] Workflow UI — `frontend/src/pages/RunsPage.tsx`
- [x] Findings review UI — `frontend/src/pages/FindingsPage.tsx` (per-finding approve/reject/edit + commit)
- [x] Report viewer — `frontend/src/pages/ReportPage.tsx`

Vite + React 19 + TypeScript + react-router-dom. `npm run build`
(tsc -b + vite build) executes clean with zero type errors;
`oxlint` reports zero errors. Never run against a live backend in
this environment (no Postgres available) — see `PROGRESS.md` for the
exact verification level of each piece and what a live round-trip
would still need to confirm. One backend addition was needed and
made: `GET /documents` (a list endpoint didn't exist before).

## Phase D — deferred per instruction

- [ ] Authentication
- [ ] Authorization
- [ ] Audit logging
- [ ] Metrics
- [ ] Export APIs
