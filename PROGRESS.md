# Docsnary — Vertical Slice Progress

Status legend: PLANNED / IN_PROGRESS / IMPLEMENTED / TESTED / BLOCKED / DEFERRED

"TESTED" means a test for this behavior was actually executed and
passed in the environment doing the work. Where noted below, code was
written and statically verified (imports, mapper configuration, API
schema resolution, or direct execution against SQLite/fakeredis
stand-ins) but the corresponding Postgres/pgvector-backed test could
not be executed because this environment has no Postgres available
(no docker, no local Postgres binaries, network restricted to package
registries). Those items are marked IMPLEMENTED, not TESTED, and this
is called out explicitly rather than being papered over.

> **Update, confirmed by the user against real infrastructure:** the
> full vertical slice (T050-T110) has been run for real — `python
> scripts/demo.py` completed successfully end to end, and `pytest -v`
> reported **101 passed**. Every item below previously marked
> IMPLEMENTED/"not executed here" for lack of a local Postgres is now
> confirmed working; this file is not being retroactively rewritten
> line-by-line to say TESTED everywhere, but that confirmation
> supersedes the "not executed" caveats throughout T050-T110 below.
> See the **Phase A** section at the end of this file for the
> real-provider work added after that confirmation.

## Pre-existing (T001-T043) — unchanged this pass

| Area | Status |
|---|---|
| FastAPI app, config, CORS, request-ID middleware, health/ready | TESTED (pre-existing) |
| Document/version upload, versioning, content-hash dedup, storage | TESTED (pre-existing) |
| Parsing (txt/pdf) | TESTED (pre-existing) |
| LangGraph workflow shape, retry/escalation routing | TESTED (pre-existing) |
| Postgres checkpointer (crash/resume at the graph level) | TESTED (pre-existing) |
| AI provider abstraction, MockAIProvider | TESTED (pre-existing) |
| Prompt injection defense (trust-boundary message + fixture) | TESTED (pre-existing) |

**Bug fixed this pass:** `app/schemas/document.py` had duplicate
repository code accidentally appended, referencing undefined names.
This broke `app.main` import entirely — the API could not start.
Removed; verified the app now imports and all routes register.

**Environment gap found and worked around:** `PromptManager` requires
a `prompts/` directory as a sibling of the backend (`DOCSNARY/prompts/`
per the project's described structure) containing `<name>/v1.txt`
files for `classification`, `extraction`, `conflict_detection`,
`validation`, `reporting`. This directory was not included in the
supplied `backend.zip`, so `app.main` and the workflow's `extract_node`
could not run at all. Minimal, clearly-labeled scaffold prompt files
were created and are included in the delivered archive under
`prompts/` — **place this folder at your repository root, next to
`backend/`**, or replace its contents with your team's real prompts if
they already exist elsewhere. `conflict_detection` and `validation`
are intentionally placeholder/reserved (see note below).

## T050 — Evidence

| Status | Verification |
|---|---|
| TESTED | Model, migration, repository, service, API, and tests were written and executed against SQLite in a prior pass. Full Postgres-backed API test suite (`tests/test_evidence.py`) written but not re-executed this pass. |

## T051-T054 — Chunking, Embeddings, pgvector Retrieval, Context Builder

| Item | Status | Verification |
|---|---|---|
| Deterministic, page-aware chunking (`app/chunking/`) | TESTED | Executed directly: stable hashes across re-chunking, correct page/paragraph splitting, plain-text fallback. |
| Embedding provider abstraction + deterministic provider | TESTED | Executed directly: deterministic, dimension-correct, self-similarity 1.0, distinguishes unrelated text. |
| `Chunk` model + pgvector column + migration | IMPLEMENTED | `cosine_distance()` API verified against the installed `pgvector==0.4.1` package; SQLAlchemy mapper configuration verified. Not run against a live Postgres/pgvector instance. |
| `ChunkRepository.search` (top-k similarity) | IMPLEMENTED | Not executable without Postgres+pgvector. |
| `RetrievalService` (chunk+embed persistence, context building, evidence-to-chunk grounding) | IMPLEMENTED | Logic reviewed; covered by `tests/test_vertical_slice.py::test_retrieval_returns_relevant_chunk_for_query`, not executed here. |

## T060 — Conflict Detection

| Status | Verification |
|---|---|
| IMPLEMENTED | `app/services/conflict.py`: numeric-aware value comparison, never overwrites the existing value, persists both sides with their evidence. Covered by `test_conflict_detection_reject_and_partial_approval`; not executed here. |

## T061 — Deterministic Rule Validation

| Status | Verification |
|---|---|
| TESTED | `app/rules/engine.py` — required fields, evidence presence, date validity, amount validity. Executed directly, including the zero-findings clean-corpus case. No LLM call involved, per project guidance. |

## T063/T070/T071 — Findings, Human Review

| Item | Status | Verification |
|---|---|---|
| Finding generation (conflict / extraction / rule_violation) | IMPLEMENTED | `app/services/finding.py`. Covered by `tests/test_vertical_slice.py`; not executed here. |
| Item-level approve/reject/edit | IMPLEMENTED | `app/services/review.py`. A committed finding cannot be re-decided (tested in `test_committed_finding_cannot_be_re_decided`, not executed here). |
| Review API (`/findings`, `/findings/{id}/decide`) | IMPLEMENTED | Route registration verified via OpenAPI schema generation; not exercised against a live DB. |

## T072 — Crash / Resume

| Status | Verification |
|---|---|
| IMPLEMENTED | Reuses the pre-existing, already-TESTED PostgresSaver checkpointer unchanged. The pause/resume pattern (`update_state` + re-`invoke` with the same `thread_id`) was verified as a standalone script against the actual installed `langgraph==1.2.11` package (see conversation) and confirmed to correctly route through to commit on resume. `RunService.finalize_review` wires this into the real review/commit flow; `test_workflow_checkpoint_persists_between_sessions` exercises it against a real DB but was not executed here. |

## T073 — Commit

| Status | Verification |
|---|---|
| IMPLEMENTED | `app/services/commit.py` — approved-only, idempotent via a unique constraint on `finding_id` in `commit_events`. Covered by `test_commit_is_idempotent`; not executed here. |

## T080 — Incremental Update

| Status | Verification |
|---|---|
| IMPLEMENTED | Reuses `run()` unchanged for a new document version. Unaffected fields are explicitly skipped from findings generation when the newly extracted value matches the committed value (`ConflictService.unchanged_fields`), so approving a run never rewrites fields that did not change. Covered by `test_incremental_update_preserves_unaffected_fields`; not executed here. |

## T080-T083 — Async Queue

| Item | Status | Verification |
|---|---|---|
| Redis run queue (`app/queue/run_queue.py`) with duplicate-event/idempotency protection | TESTED | Executed directly against `fakeredis`: enqueue/dequeue round-trip, duplicate idempotency-key rejection, empty-queue timeout. |
| Worker process (`app/workers/run_worker.py`) | IMPLEMENTED | Single-process consumer loop calling `RunService.run` per job. Not run as a live daemon in this environment. |
| File-watcher / auto-ingestion | DEFERRED | Not part of the minimum viable Task 1 demo; requires a host filesystem-watching daemon out of scope for this pass. |

## T090 — Docsnary MCP

| Status | Verification |
|---|---|
| IMPLEMENTED / partially TESTED | `app/mcp/server.py` — 7 tools (`list_documents`, `start_run`, `get_run_status`, `list_findings`, `decide_finding`, `finalize_review`, `get_case_report`), each a thin adapter opening its own DB session and calling the same application services as the REST API. No domain logic lives in the MCP layer. Tool registration was executed and verified directly (all 7 tools present with correct names). The full DB-backed end-to-end MCP flow test (`tests/test_mcp_server.py`) was written but not executed here. |

## T100 — Contract Register Domain (Task 1 domain)

| Status | Verification |
|---|---|
| IMPLEMENTED | Fixture corpus at `tests/fixtures/contract_corpus/`: `contract_v1.txt`, `invoice.txt`, `renewal_notice.txt` (contains a deliberate `$100,000` vs `$120,000` contradiction), `contract_v2_amendment.txt` (a legitimate incremental change — extended `end_date` only). A real, reusable, fully offline `DeterministicKeyValueAIProvider` (`app/integrations/ai/deterministic.py`) parses these — executed directly and confirmed to produce correct, per-document structured facts, and confirmed immune to the existing prompt-injection fixture (produces zero facts rather than following embedded instructions). |

## T110 — Resilience Tests

| Test file | Status |
|---|---|
| `tests/test_evidence.py` | Written in a prior pass; not re-executed this pass. |
| `tests/test_vertical_slice.py` | Written this pass: full run + evidence + chunks, retrieval relevance, missing-document 404, rule violations, clean-corpus zero-violations, conflict detection + reject + partial approval, idempotent commit, committed-finding-immutable, checkpoint persistence across sessions, incremental update preserving unaffected fields, prompt-injection immunity. **Not executed** — requires live Postgres/pgvector. |
| `tests/test_mcp_server.py` | Written this pass: tool registration (**executed and passing**), full MCP flow against a live DB (not executed). |
| `tests/test_run_queue.py` | Written and **executed against fakeredis — all 3 tests passing**. |

## T110 — Full Demo

| Status | Verification |
|---|---|
| IMPLEMENTED | `scripts/demo.py` — runs the complete flow described in the "Working Demo" section of the final report. Syntax-checked and manually traced against the actual service signatures; **not executed end-to-end** (requires live Postgres/pgvector/Redis, unavailable in this environment). |

## Explicitly Deferred (not part of this vertical slice)

- Full React review UI (backend API only, per project guidance)
- Real embedding/LLM provider integration (deterministic providers only; swapping one in is a one-file change per provider's factory)
- File-watcher / auto-ingestion pipeline
- Worker horizontal scaling, retry/backoff policy, dead-letter queue
- Enterprise auth, observability platform, cloud deployment infra
- Advanced pgvector indexing (ivfflat/hnsw) — the column exists and is queried correctly; an index is a pure performance optimization deferred until real data volume justifies it
- Narrative LLM-generated case reports (the `reporting` prompt is a reserved placeholder; the current `/cases/{case_id}/report` endpoint assembles the report directly from the database)

## Immediate Next Step for the Team

Run `docker-compose up -d && alembic upgrade head` in a real environment,
then `pytest` and `python scripts/demo.py` to convert every
"IMPLEMENTED" line above to "TESTED". This environment could not do
that step — no Postgres/pgvector/Redis and no way to install them
here.

---

## Phase A — Real AI Providers, Real Embeddings, Token Usage Tracking

Status legend as above. This section covers only what changed in this
pass; everything above this line reflects the prior, now-confirmed-
working vertical slice.

| Item | Status | Verification |
|---|---|---|
| `OpenAIProvider` (`app/integrations/ai/openai_provider.py`) | TESTED (mocked client) | JSON-schema constrained chat completions; SDK exceptions mapped to `AIProviderError` subclasses; happy-path + invalid-JSON tests pass. Not tested against the live OpenAI API (no key available here). |
| `AnthropicProvider` (`app/integrations/ai/anthropic_provider.py`) | TESTED (mocked client) | Structured output via forced tool-use (Anthropic has no native JSON mode); happy-path + missing-tool-use tests pass. Not tested against the live API. |
| `GeminiProvider` (`app/integrations/ai/gemini.py`) | TESTED (mocked client) | Native `response_mime_type=application/json`; happy-path + invalid-JSON tests pass. Not tested against the live API. |
| `create_ai_provider()` factory | TESTED | All three real providers now selectable via `AI_PROVIDER`; imports are lazy so the app still runs with zero real-provider SDKs configured. Confirmed all three instantiate without a network call. |
| `OpenAIEmbeddingProvider` (`app/integrations/embeddings/openai_embeddings.py`) | IMPLEMENTED | Uses OpenAI's `dimensions` truncation parameter so output size always matches `settings.embedding_dimensions`. Not tested against the live API. |
| `EMBEDDING_DIMENSIONS` config | TESTED | Moved from a hardcoded `32` in `app/models/chunk.py` to `settings.embedding_dimensions` (still defaults to 32 — zero behavior change out of the box). Confirmed the default embedding provider still resolves to 32-dim `DeterministicEmbeddingProvider` unchanged. |
| Migration `c4a8f0e1d6b2` (alter chunk embedding dimension) | IMPLEMENTED | Dynamically alters the `chunks.embedding` column to `settings.embedding_dimensions` at upgrade time; no-op if unchanged (the common case). Not run against a live DB here. |
| `scripts/reembed_chunks.py` | IMPLEMENTED | Batch re-embeds all existing chunks with whatever provider is currently configured. Not run here. |
| Cost estimation (`app/integrations/ai/pricing.py`) | TESTED | Static per-model pricing table + prefix-match fallback for dated model names. **Bug found and fixed during testing**: prefix matching originally picked the first matching (shorter, wrong) prefix — e.g. `gpt-4o-mini-2026-08-01` matched `gpt-4o` pricing instead of `gpt-4o-mini`. Fixed to prefer the longest/most-specific match; regression test added and passing. |
| `extract_node` cost wiring | TESTED | `usage.estimated_cost` in the LangGraph state was previously always `0.0`; now accumulates real per-call cost via the pricing module. All 14 pre-existing `test_agent_workflow.py` tests still pass unchanged (pure-function node tests, no behavior change for mock/deterministic providers, which correctly price at $0). |
| Run-level usage persistence | IMPLEMENTED | `runs.input_tokens` / `output_tokens` / `estimated_cost` columns (migration `d5b7c3a9f1e4`), written in `RunService.run()` right after the graph call, exposed via `GET /runs/{run_id}` and the MCP `get_run_status` tool. `test_run_persists_token_usage_estimate` written; not executed here (needs live Postgres). |

### Files added/changed this pass

- `app/integrations/ai/openai_provider.py`, `anthropic_provider.py`, `gemini.py`, `pricing.py` (new)
- `app/integrations/ai/factory.py` (extended)
- `app/integrations/embeddings/openai_embeddings.py` (new)
- `app/integrations/embeddings/factory.py` (extended)
- `app/models/chunk.py`, `app/models/run.py` (extended)
- `app/repositories/run.py` (extended: `record_usage`)
- `app/services/run.py` (usage persistence wired in)
- `app/schemas/run.py` (extended: `RunStatusResponse` usage fields)
- `app/core/config.py` (`embedding_model`, `embedding_dimensions`; existing `ai_*` settings unchanged)
- `alembic/versions/c4a8f0e1d6b2_...py`, `d5b7c3a9f1e4_...py` (new)
- `scripts/reembed_chunks.py` (new)
- `tests/test_real_ai_providers.py` (new, 10 tests, all passing)
- `tests/test_vertical_slice.py` (+1 test: usage persistence)
- `requirements.txt`, `.env` (documented new provider options)

### Known limitations of Phase A

- None of the three real providers or the real embedding provider have been exercised against a live API — this requires actual API keys, which are not available in this environment. The mocked-client tests validate request construction, response parsing, and error mapping, but not live-service behavior (rate limits, actual latency, model-specific quirks in structured output compliance).
- Anthropic's forced-tool-use approach to structured output is the standard pattern but has not been validated against Anthropic's actual schema-validation behavior for complex nested schemas.
- `EMBEDDING_DIMENSIONS=32` remains the default. For real production-quality embeddings, set it to at least 512-1536 in `.env`, run migration `c4a8f0e1d6b2`, and re-embed via `scripts/reembed_chunks.py` — this was written but not exercised end-to-end here.
- Cost estimates are a point-in-time snapshot and will drift as providers change pricing; they are explicitly documented as non-billing-grade.

### Immediate next step

Set a real `AI_API_KEY` + `AI_PROVIDER=openai|anthropic|gemini` (or `EMBEDDING_PROVIDER=openai`) in `.env`, run `alembic upgrade head`, and re-run `pytest tests/test_real_ai_providers.py -v` plus `python scripts/demo.py` with a real provider to convert the remaining IMPLEMENTED items to TESTED.

---

## Phase B — Real Document Processing

| Item | Status | Verification |
|---|---|---|
| DOCX parser (`app/parsing/docx.py`) | TESTED | Paragraph extraction, explicit page-break detection (`<w:br w:type="page"/>`), table extraction as separate pages. 7 tests, all executed and passing, including rejection of invalid DOCX bytes. |
| OCR fallback in `PdfParser` (`app/parsing/pdf.py`) | TESTED | Pages with no extractable text layer are rendered to an image and OCR'd via tesseract; pages with real text are left untouched (confirmed via `ocr_page_count`). **Executed against a real image-only PDF page and real tesseract OCR** — not mocked. |
| Standalone image OCR parser (`app/parsing/image_ocr.py`) | TESTED | PNG/JPEG/TIFF support. Executed end-to-end against a real rendered image with real tesseract OCR, correctly extracting the text. |
| Page-aware evidence references | IMPLEMENTED | `RunService.run()`'s evidence-to-chunk grounding step (already existed for T054) now also overwrites `Evidence.location` with the real `page {N}` derived from the matched chunk's `page_index` — authoritative because it comes from parser-level page structure (PDF/DOCX/OCR), not from what the extraction step self-reported. A dedicated test (`test_evidence_location_reflects_real_pdf_page`) was written using a real 2-page PDF; see Known Limitations for its execution status. |
| Factory wiring (`app/parsing/factory.py`) | TESTED | DOCX and image content-types/extensions now resolve to the correct parser; a genuinely unsupported format still raises `UnsupportedDocumentError`. |

### Environment note

Real tesseract 5.3.4 was available and used for all OCR tests in this
environment (`apt-get install tesseract-ocr` succeeded). If your
deployment target doesn't have tesseract installed, `ImageOcrParser`
and the PDF OCR fallback raise a clear `DocumentParseError` naming the
missing binary rather than crashing unhelpfully — but OCR simply
won't work until it's installed (`apt-get install tesseract-ocr` on
Debian/Ubuntu, `brew install tesseract` on macOS).

### Files added/changed this pass

- `app/parsing/docx.py`, `app/parsing/image_ocr.py` (new)
- `app/parsing/pdf.py` (extended with OCR fallback)
- `app/parsing/factory.py` (extended)
- `app/services/run.py` (page-aware evidence grounding)
- `tests/test_parsing_phase_b.py` (new, 16 tests, all executed and passing)
- `tests/test_parsing.py` (1 pre-existing test updated: `image/png` is no longer an "unsupported format" example now that OCR image parsing exists — replaced with a genuinely unsupported type)
- `requirements.txt` (`python-docx`, `pytesseract`, `Pillow`)

### Known limitations of Phase B

- DOCX page-break detection only recognizes explicit page breaks (`Ctrl+Enter`/"Insert Page Break"). Word's automatic pagination based on content overflow (what you see when scrolling a long document without ever pressing a page-break key) is not detectable from the file format itself — this is a fundamental DOCX limitation, not a gap in the parser. Real-world contracts with explicit section/page breaks (the common case for formal documents) are handled correctly.
- OCR quality depends on scan quality and tesseract's default settings (no image preprocessing/deskew/binarization added). For low-quality scans, consider adding OpenCV-based preprocessing as a future enhancement.
- The deterministic key-value demo/test AI provider expects clean `Label: value` lines; OCR noise (e.g. a dropped colon) can cause it to miss a field it would have caught in a clean text document. This is a limitation of that specific *test* provider's simplistic regex, not of extraction in general — a real LLM provider (Phase A) handles OCR noise far more gracefully via semantic understanding rather than exact pattern matching.
- A dedicated test for page-aware evidence grounding was added
  (`test_evidence_location_reflects_real_pdf_page` in
  `tests/test_vertical_slice.py`): a real 2-page PDF is built with
  pymupdf, uploaded, run, and the resulting `Evidence.location` values
  are asserted to read `"page 1"` / `"page 2"` matching which page
  each fact's text actually came from. Written and reviewed carefully
  against the exact chunking/grounding code path, but **not executed
  here** — needs live Postgres/pgvector like the rest of the
  DB-dependent suite.

### Immediate next step

Upload a real scanned PDF or DOCX contract through the API and confirm in `/documents/{id}/evidence` that `location` values read `"page N"` derived from actual page structure, not guessed by the extraction step.

---

## Phase C — React Frontend

A single-page app (`frontend/`, Vite + React 19 + TypeScript, react-router-dom)
with the four screens requested: Documents (upload), Runs (workflow), Findings
Review, and Case Report (register viewer).

| Item | Status | Verification |
|---|---|---|
| Upload UI (`DocumentsPage.tsx`) | TESTED (build/type-check) | Lists documents via new `GET /documents` endpoint, upload form posts to existing `POST /documents`, hands off to the Runs page on success. |
| Workflow UI (`RunsPage.tsx`) | TESTED (build/type-check) | Version picker (`GET /documents/{id}/versions`), starts a run (`POST /runs`), shows status + token usage/cost (`GET /runs/{run_id}`), run-ID lookup for resuming a session. |
| Findings Review UI (`FindingsPage.tsx`) | TESTED (build/type-check) | Per-finding approve/reject/edit (`POST /findings/{id}/decide`), commit button (`POST /runs/{run_id}/finalize`) disabled while findings remain pending, shows commit result breakdown. |
| Report viewer (`ReportPage.tsx`) | TESTED (build/type-check) | Renders the canonical register (`GET /cases/{case_id}/report`) as a sorted table. |
| Typed API client (`src/lib/api.ts`) | TESTED (build/type-check) | One function per backend endpoint used, response shapes matched exactly against the Pydantic schemas; error parsing matched against `AppError`'s actual JSON response shape (`{"error": {"code", "message"}}`). |
| Production build | **TESTED — actually executed** | `npm run build` (tsc -b + vite build) succeeds with zero type errors on a clean build. `npx tsc -b --force` re-run standalone to confirm no swallowed errors. `npx oxlint src/` — 0 errors (2 harmless idiomatic warnings, not fixed, explained in code). `vite preview` served and `curl`-verified (200 OK on index.html and the built JS bundle). |
| Backend change: `GET /documents` | TESTED | Added because no endpoint existed to list documents (only upload/get-by-id) — needed by the Documents page. Reuses the existing `DocumentService`/`DocumentRepository` (Phase A already added `list_documents`/`list_all` for the MCP server). New `DocumentSummaryResponse`/`DocumentListResponse` schemas. `test_list_documents_api` written; not executed here (needs live Postgres) — but the route registration itself was confirmed via OpenAPI schema generation. |

### What was NOT run

The frontend was never pointed at a live backend in this environment
(same Postgres/pgvector unavailability as every prior phase) — so
while the build is genuinely verified (real `tsc`, real `vite build`,
real `oxlint`, real HTTP serve-and-fetch of the built assets), no
actual document was ever uploaded through the UI and no real
API round-trip against the FastAPI app has been observed. The type
contracts between frontend and backend were checked by hand,
field-by-field, against the actual Pydantic schemas and the actual
`AppError` handler — not run against each other live.

### Files added

- `frontend/` — full Vite project (`src/lib/api.ts`, `src/lib/CaseContext.tsx`, `src/components/StatusStamp.tsx`, `src/pages/{Documents,Runs,Findings,Report}Page.tsx`, `src/App.tsx`, `src/main.tsx`, `src/styles/{tokens,components}.css`, `.env.example`, `README.md`)
- `app/schemas/document.py` (+`DocumentSummaryResponse`, `DocumentListResponse`)
- `app/api/routers/documents.py` (+`GET /documents`)
- `tests/test_vertical_slice.py` (+`test_list_documents_api`, `TestClient` now imported)

### Known limitations of Phase C

- No live frontend-to-backend round trip observed (see above).
- No authentication — anyone with network access to the API can act as any reviewer identity (a free-text field). This is explicitly Phase D.
- No real-time updates — a long-running run's status must be manually refreshed (re-fetch), not pushed. Acceptable for this scale; would need polling or a websocket for a production multi-user deployment.
- No document preview pane (view the actual PDF/DOCX/image inline) — evidence quotes and page numbers are shown as text, not overlaid on a rendered page. A reasonable next enhancement.
- Case ID is a free-text field with no autocomplete/validation against existing cases; a typo silently starts reviewing an empty/wrong register.

### Immediate next step

Start the backend (`uvicorn app.main:app --reload`) and the frontend
(`cd frontend && npm run dev`) together and walk through the full
flow once by hand: upload `tests/fixtures/contract_corpus/contract_v1.txt`,
start a run, approve the findings, commit, and confirm the Case Report
page shows the committed register.
