# DOCSNARY — TASK 1.md

## Purpose

This file is the implementation checklist for **DocsNary — Task 1** of the SuperDocs assignment.

- `ARCHITECTURE.md` defines **what the system is and how it should work**.
- `TASK 1.md` defines **what needs to be built for Task 1**.
- `PROGRESS.md` records **what has actually been completed**.

This file is intentionally **Task 1 only**.

### Task 1
Build DocsNary's own agentic document-analysis system.

### Task 2
The separate SuperDocs-based **Win/Loss Debrief + Quarterly Competitive Brief** use case is NOT part of this file.

Do not restart completed work. The status below preserves the work already completed in the previous `TASK.md`.

---

# Status Legend

- [ ] PLANNED
- [~] IN_PROGRESS
- [x] TESTED / COMPLETE
- [!] BLOCKED
- [-] DEFERRED

---

# Definition of Done

A task may be marked `[x]` only when applicable items below are complete:

- implementation exists
- API contract exists if applicable
- database changes exist if applicable
- error handling exists
- tests exist
- security implications are considered
- workflow behavior is verified
- UI is updated if applicable
- documentation is updated
- implementation actually works in a fresh/reproducible environment

---

# IMPORTANT: Current Project Position

The previous Task 1 checklist shows that the following foundation is already complete:

- Project foundation
- Local PostgreSQL/pgvector/Redis infrastructure
- FastAPI foundation
- Backend module boundaries
- Database foundation
- Document upload/storage/versioning/parsing
- LangGraph state/workflow
- Retry/escalation
- Checkpoint/resume
- AI provider abstraction
- Prompt management
- Structured extraction
- Prompt-injection defense

Therefore:

> **Do NOT restart from T001.**

The next major implementation area is **Phase 5 — Evidence and Retrieval**, beginning with `T050`.

The remaining phases have been cleaned up so Task 1 can be completed without building the Task 2 Win/Loss domain.

---

# PHASE 0 — PROJECT FOUNDATION

## T001 — Repository structure

- [x] Create `backend/`
- [x] Create `frontend/`
- [x] Create `prompts/`
- [x] Create `tests/`
- [x] Create `docs/`
- [x] Create `diagrams/`
- [x] Create `examples/`
- [x] Create root documentation files

**Depends on:** none

---

## T002 — Root documentation

- [x] `README.md`
- [x] `ARCHITECTURE.md`
- [x] `TASK 1.md`
- [x] `PROGRESS.md`
- [x] `.env.example`
- [x] `.gitignore`

**Depends on:** T001

> Note: The original checklist called this `TASK.md`. This cleaned version is the Task 1 checklist. If the repository still uses `TASK.md`, keep the filename you prefer; the important point is that it contains Task 1 only.

---

## T003 — Local infrastructure

- [x] Docker Compose configuration
- [x] PostgreSQL service
- [x] pgvector support
- [x] Redis service
- [x] health checks
- [x] documented startup commands

**Depends on:** T001

---

# PHASE 1 — BACKEND FOUNDATION

## T010 — FastAPI application

- [x] FastAPI app
- [x] application configuration
- [x] environment loading
- [x] API versioning
- [x] `/health`
- [x] `/ready`
- [x] structured error handling
- [x] CORS configuration
- [x] request IDs
- [x] automated tests

**Depends on:** T003

---

## T011 — Backend module boundaries

- [x] API routers
- [x] schemas
- [x] application services
- [x] domain models
- [x] repositories
- [x] infrastructure adapters
- [x] integrations
- [x] core configuration

**Depends on:** T010

---

## T012 — Database foundation

- [x] PostgreSQL connection
- [x] migrations
- [x] repository pattern
- [x] transaction handling
- [x] base model conventions

**Depends on:** T010, T003

---

# PHASE 2 — DOCUMENT MANAGEMENT

## T020 — Document upload

- [x] upload endpoint
- [x] file validation
- [x] metadata validation
- [x] content hash
- [x] document record
- [x] document version record

**Depends on:** T012

---

## T021 — File/object storage

- [x] storage abstraction
- [x] local development storage
- [x] object storage-compatible adapter
- [x] original document persistence
- [x] storage metadata

**Depends on:** T020

---

## T022 — Document versioning

- [x] immutable versions
- [x] version numbering
- [x] parent version relationship
- [x] duplicate-content detection
- [x] version retrieval API

**Depends on:** T020, T021

---

## T023 — Document parsing

- [x] parser abstraction
- [x] text extraction
- [x] page/section metadata
- [x] unsupported-format handling
- [x] parser tests

**Depends on:** T021

---

# PHASE 3 — AGENT FOUNDATION

## T030 — LangGraph state

- [x] define typed agent state
- [x] run ID
- [x] document/version IDs
- [x] extracted facts
- [x] evidence
- [x] conflicts
- [x] validation results
- [x] findings
- [x] proposed changes
- [x] review status
- [x] retry state
- [x] errors
- [x] usage/cost state

**Depends on:** T012, T023

---

## T031 — LangGraph workflow

- [x] START
- [x] ingest node
- [x] classify node
- [x] extract node
- [x] output validation
- [x] conflict detection
- [x] rule validation
- [x] finding generation
- [x] human review gate
- [x] commit
- [x] END

**Depends on:** T030

---

## T032 — Retry and escalation

- [x] bounded retry
- [x] retry counter
- [x] retry reason
- [x] escalation state
- [x] terminal failure handling
- [x] retry tests

**Depends on:** T031

---

## T033 — Checkpoint/resume

- [x] persistent workflow checkpoints
- [x] restart test
- [x] completed nodes skipped
- [x] failed node resumed
- [x] checkpoint integrity

**Depends on:** T031, T032

---

# PHASE 4 — AI / EXTRACTION

## T040 — AI provider abstraction

- [x] provider interface
- [x] model configuration
- [x] timeout
- [x] retry normalization
- [x] structured output support
- [x] usage capture
- [x] provider error normalization
- [x] tests
- [x] full suite verification

**Depends on:** T030

---

## T041 — Prompt management

- [x] classification prompt
- [x] extraction prompt
- [x] conflict prompt
- [x] validation prompt
- [x] reporting prompt
- [x] prompt version identifiers
- [x] prompt metadata recorded per run

**Depends on:** T040

---

## T042 — Structured extraction

- [x] extraction schema
- [x] model invocation
- [x] schema validation
- [x] confidence score
- [x] evidence references
- [x] invalid-output retry

**Depends on:** T041, T031

---

## T043 — Prompt injection defense

- [x] explicit document-content boundaries
- [x] system/application instruction separation
- [x] untrusted document handling
- [x] no document-driven arbitrary tool execution
- [x] injection fixture
- [x] injection test

**Depends on:** T042

---

# PHASE 5 — EVIDENCE AND RETRIEVAL

> **NEXT MAJOR IMPLEMENTATION AREA**

## T050 — Evidence model

- [ ] evidence entity
- [ ] source document reference
- [ ] source version
- [ ] source location
- [ ] chunk reference
- [ ] evidence API
- [ ] evidence persistence tests

**Depends on:** T023, T042

---

## T051 — Chunking

- [ ] chunking strategy
- [ ] chunk metadata
- [ ] page/section preservation
- [ ] deterministic chunk IDs
- [ ] chunking tests

**Depends on:** T023

---

## T052 — Embeddings

- [ ] embedding provider abstraction
- [ ] embedding generation
- [ ] embedding persistence
- [ ] retry handling
- [ ] mocked embedding tests
- [ ] deterministic/fake embedding provider for tests

**Depends on:** T051

---

## T053 — pgvector retrieval

- [ ] vector column
- [ ] vector index
- [ ] semantic search
- [ ] metadata filtering
- [ ] top-k retrieval
- [ ] retrieval tests

**Depends on:** T052, T003

> Do not treat PostgreSQL full-text search as equivalent to vector search. If time is limited, keep the pgvector architecture and simplify the sophistication of ranking/embeddings rather than claiming FTS satisfies the vector-search requirement.

---

## T054 — Context builder

- [ ] retrieve relevant evidence
- [ ] rank/filter context
- [ ] preserve source references
- [ ] pass structured context to AI
- [ ] context-builder tests

**Depends on:** T050, T053

---

# PHASE 6 — CONFLICTS AND RULES

## T060 — Conflict detection

- [ ] compare new facts with existing facts
- [ ] identify contradictory values
- [ ] create conflict records
- [ ] attach evidence from both sides
- [ ] preserve both conflicting values
- [ ] conflict tests

**Depends on:** T042, T050, T054

---

## T061 — Rule representation

- [ ] rule representation
- [ ] required-field checks
- [ ] source/evidence checks
- [ ] date validation
- [ ] amount validation
- [ ] domain-rule interface
- [ ] rule versioning
- [ ] rule tests

**Depends on:** T042, T050

---

## T062 — Rule ingestion and execution

- [ ] accept user-provided rule sets
- [ ] validate rule configuration
- [ ] version rule sets
- [ ] execute rules against source documents
- [ ] execute rules against generated deliverable
- [ ] attach evidence to rule findings
- [ ] support clean corpus → zero findings
- [ ] rule execution tests

**Depends on:** T061, T054

---

## T063 — Findings

- [ ] finding model
- [ ] confidence
- [ ] severity
- [ ] evidence references
- [ ] proposed action
- [ ] finding status
- [ ] finding tests

**Depends on:** T060, T062

---

# PHASE 7 — HUMAN REVIEW AND COMMIT

## T070 — Findings API

- [ ] finding persistence
- [ ] list findings
- [ ] get finding
- [ ] filter by status/severity
- [ ] finding API tests

**Depends on:** T063

---

## T071 — Review API

- [ ] list findings
- [ ] get finding
- [ ] approve
- [ ] reject
- [ ] edit where supported
- [ ] review comments
- [ ] reviewer identity
- [ ] authorization
- [ ] review API tests

**Depends on:** T070

---

## T072 — Human review gate

- [ ] pause graph
- [ ] persist review state
- [ ] resume graph
- [ ] item-level decisions
- [ ] mixed approve/reject behavior
- [ ] verify rejecting one finding does not affect another

**Depends on:** T071, T033

---

## T073 — Commit layer

- [ ] approved-only commit
- [ ] rejected changes excluded
- [ ] idempotent commit
- [ ] version record
- [ ] audit event
- [ ] commit failure handling
- [ ] transaction tests

**Depends on:** T072

---

# PHASE 8 — ASYNC PROCESSING

## T080 — Redis queue

- [ ] queue abstraction
- [ ] job creation
- [ ] job status
- [ ] retry scheduling
- [ ] duplicate-event protection
- [ ] queue tests

**Depends on:** T003, T012

---

## T081 — Background worker

- [ ] worker process
- [ ] job dispatcher
- [ ] document processing handler
- [ ] AI processing handler
- [ ] report handler
- [ ] graceful shutdown

**Depends on:** T080, T031

---

## T082 — Async API

- [ ] create run
- [ ] return `run_id`
- [ ] queue job
- [ ] run status endpoint
- [ ] job status endpoint
- [ ] error status

**Depends on:** T081

---

## T083 — File watcher

- [ ] watched-folder configuration
- [ ] new-file detection
- [ ] modification detection
- [ ] content hash
- [ ] duplicate-event handling
- [ ] enqueue processing job

**Depends on:** T080, T021

---

# PHASE 9 — INCREMENTAL PROCESSING

## T090 — Change detection

- [ ] compare content hashes
- [ ] identify changed version
- [ ] preserve previous version
- [ ] create update event

**Depends on:** T022, T083

---

## T091 — Incremental extraction

- [ ] process only changed content
- [ ] preserve unchanged facts
- [ ] update affected facts
- [ ] identify affected findings
- [ ] incremental extraction tests

**Depends on:** T090, T042, T060

---

## T092 — Incremental commit

- [ ] update only affected deliverable areas
- [ ] preserve approved unchanged content
- [ ] audit changed sections
- [ ] test repeated updates
- [ ] verify unaffected sections remain unchanged/byte-identical where practical

**Depends on:** T091, T073

---

## T093 — New-document conflict scenario

- [ ] new document contradicts existing conclusion
- [ ] system surfaces conflict
- [ ] existing conclusion is not silently overwritten
- [ ] evidence from old and new documents is shown

**Depends on:** T091, T060

---

## T094 — Incremental audit/history

- [ ] show what changed
- [ ] show when it changed
- [ ] show which document caused the change
- [ ] preserve previous versions

**Depends on:** T092, T140

---

# PHASE 10 — SIMPLE TASK 1 DOMAIN VERTICAL SLICE

> This is intentionally small. It exists to prove the generic agentic engine.
>
> **Domain: Vendor Contract & Invoice Reconciliation**
>
> Do NOT build a complete contract-management product.

## Example corpus

Use approximately 5–10 small documents:

- vendor contract
- contract amendment
- invoice
- second invoice
- renewal notice

Include at least one deliberate contradiction.

Example:

```text
Original contract:  $100,000
Amendment:          $120,000
Invoice:            $130,000
```

The exact values do not matter. The important thing is that the system can identify the contradiction and show evidence for all sides.

---

## T100 — Contract register schema

- [ ] vendor
- [ ] contract value
- [ ] start date
- [ ] end date
- [ ] renewal date
- [ ] invoice amount
- [ ] status
- [ ] evidence reference for every important field

**Depends on:** T050, T054

---

## T101 — Simple domain corpus

- [ ] create/use synthetic or public contract documents
- [ ] include contract
- [ ] include amendment
- [ ] include invoice(s)
- [ ] include renewal notice
- [ ] include deliberate contradiction

**Depends on:** T020, T023

---

## T102 — Contract analysis

- [ ] run full agentic workflow over corpus
- [ ] classify documents
- [ ] extract facts
- [ ] retrieve evidence
- [ ] reconcile facts
- [ ] detect conflicts
- [ ] generate grounded report

**Depends on:** T060, T054, T100, T101

---

## T103 — Rule validation scenario

- [ ] provide a small user rule set
- [ ] validate source documents
- [ ] validate generated report
- [ ] produce findings
- [ ] correctly support zero findings
- [ ] attach evidence to rule findings

**Depends on:** T062, T102

---

## T104 — Incremental scenario

- [ ] add a new amendment/invoice
- [ ] detect changed document
- [ ] reprocess affected content
- [ ] identify changed facts
- [ ] surface new conflict if applicable
- [ ] preserve unaffected output

**Depends on:** T093, T102

---

## T105 — Task 1 vertical-slice verification

- [ ] documents → agent
- [ ] agent → evidence
- [ ] evidence → facts
- [ ] facts → conflicts/rules
- [ ] conflicts/rules → findings
- [ ] findings → human review
- [ ] approved findings → commit
- [ ] commit → final report
- [ ] final report contains traceable evidence

**Depends on:** T100-T104, T073

---

# PHASE 11 — MCP FOR DOCSNARY

> This is **DocsNary's own MCP server**.
>
> It is NOT the SuperDocs MCP.
>
> Task 2 will separately consume SuperDocs' API/MCP.

## T110 — MCP server

- [ ] MCP server foundation
- [ ] health/startup behavior
- [ ] shared application-service integration
- [ ] MCP tests

**Depends on:** T011

---

## T111 — Core MCP tools

- [ ] upload document
- [ ] list documents
- [ ] get document
- [ ] search documents
- [ ] search evidence
- [ ] configure/upload rule set
- [ ] run analysis
- [ ] get run status
- [ ] list findings
- [ ] get finding
- [ ] approve finding
- [ ] reject finding
- [ ] export report

**Depends on:** T110, T071, T082

---

## T112 — MCP authorization and boundaries

- [ ] permission checks
- [ ] safe tool boundaries
- [ ] prevent arbitrary unsafe tool execution
- [ ] audit MCP operations

**Depends on:** T111

---

## T113 — MCP machine-driven E2E

- [ ] programmatically upload documents
- [ ] configure rules
- [ ] start analysis
- [ ] monitor run
- [ ] retrieve findings
- [ ] approve/reject findings
- [ ] export final report
- [ ] complete workflow without React UI clicks

**Depends on:** T105, T111, T112

---

# PHASE 12 — MINIMAL FRONTEND

> The UI is for demonstrating the system, not for hiding the system.

## T120 — React foundation

- [ ] React application
- [ ] routing
- [ ] API client
- [ ] environment configuration
- [ ] loading/error states

**Depends on:** T010

---

## T121 — Dashboard

- [ ] workflow summary
- [ ] recent documents
- [ ] pending reviews
- [ ] recent reports
- [ ] errors

**Depends on:** T082, T071

---

## T122 — Document UI

- [ ] upload
- [ ] document list
- [ ] versions
- [ ] metadata
- [ ] processing state

**Depends on:** T020, T022, T082

---

## T123 — Workflow UI

- [ ] run creation
- [ ] visible agent stages
- [ ] stage progress
- [ ] retry state
- [ ] failure state
- [ ] run details

**Depends on:** T082

---

## T124 — Review UI

- [ ] findings list
- [ ] evidence panel
- [ ] proposed change
- [ ] approve
- [ ] reject
- [ ] edit where supported
- [ ] review comments

**Depends on:** T071, T072

---

## T125 — Reports UI

- [ ] report list
- [ ] report viewer
- [ ] evidence links
- [ ] export
- [ ] conflict display

**Depends on:** T100-T105

---

# PHASE 13 — SECURITY

## T130 — Authentication

- [ ] authentication strategy
- [ ] login/session/token handling
- [ ] protected endpoints
- [ ] authentication tests

**Depends on:** T010

---

## T131 — Authorization

- [ ] roles/permissions
- [ ] resource-level authorization
- [ ] review permissions
- [ ] admin permissions
- [ ] authorization tests

**Depends on:** T130, T071

---

## T132 — Secrets

- [ ] `.env` ignored
- [ ] `.env.example`
- [ ] no credentials in repository
- [ ] production secret strategy documented

**Depends on:** T002

---

## T133 — Input/file safety

- [ ] file type validation
- [ ] file size limits
- [ ] safe file paths
- [ ] user-controlled content treated as data
- [ ] unsafe content cannot directly invoke tools

**Depends on:** T020, T043

---

# PHASE 14 — AUDIT / COST / OBSERVABILITY

## T140 — Audit logging

- [ ] audit event model
- [ ] run events
- [ ] document events
- [ ] review events
- [ ] commit events
- [ ] MCP events

**Depends on:** T073, T112

---

## T141 — Cost tracking

- [ ] model
- [ ] token usage
- [ ] stage timing
- [ ] estimated cost
- [ ] run summary
- [ ] cost tests

**Depends on:** T040, T031

---

## T142 — Application logging

- [ ] structured logs
- [ ] request ID
- [ ] run ID
- [ ] job ID
- [ ] document ID
- [ ] stage
- [ ] no secrets in logs

**Depends on:** T010, T081

---

## T143 — Metrics

- [ ] workflow duration
- [ ] stage duration
- [ ] queue depth
- [ ] success/failure
- [ ] retry count
- [ ] token usage
- [ ] estimated cost

**Depends on:** T141

---

## T144 — Honest success/failure

- [ ] never report success when output failed
- [ ] expose partial state clearly
- [ ] expose insufficient-evidence state
- [ ] expose terminal failure state
- [ ] test failure reporting

**Depends on:** T031, T141

---

# PHASE 15 — TESTING AND RESILIENCE

## T150 — Unit test suite

- [ ] domain tests
- [ ] parser tests
- [ ] validation tests
- [ ] evidence tests
- [ ] conflict tests
- [ ] rule tests
- [ ] cost tests

**Depends on implementation phases**

---

## T151 — Integration tests

- [ ] PostgreSQL
- [ ] pgvector
- [ ] Redis
- [ ] repositories
- [ ] FastAPI
- [ ] storage

**Depends on implementation phases**

---

## T152 — Agent workflow tests

- [ ] normal workflow
- [ ] retry
- [ ] escalation
- [ ] checkpoint
- [ ] human gate
- [ ] commit
- [ ] incremental update

**Depends on T031-T105**

---

## T153 — Required resilience tests

- [ ] crash/recovery
- [ ] concurrent runs
- [ ] duplicate event
- [ ] prompt injection
- [ ] unsupported claim
- [ ] invalid AI output
- [ ] partial approval/rejection
- [ ] failed export

**Depends on relevant implementation**

---

## T154 — No-live-API-key resilience testing

- [ ] tests run without a live LLM API key
- [ ] deterministic fake model provider
- [ ] real database used
- [ ] real workflow/checkpointing used
- [ ] real transaction behavior used
- [ ] real concurrency behavior used
- [ ] real review/commit logic used

**Depends on T153**

---

## T155 — Task 1 end-to-end test

- [ ] upload contract corpus
- [ ] process with agent
- [ ] extract evidence-backed facts
- [ ] detect deliberate conflict
- [ ] apply user rules
- [ ] generate findings
- [ ] approve/reject findings individually
- [ ] commit only approved changes
- [ ] export grounded report
- [ ] add new document
- [ ] run incremental update
- [ ] verify unaffected output remains unchanged
- [ ] run equivalent workflow through MCP

**Depends on T105, T113**

---

# PHASE 16 — DELIVERY

## T160 — Fresh clone setup

- [ ] fresh clone tested
- [ ] setup instructions verified
- [ ] Docker startup verified
- [ ] environment setup verified
- [ ] tests run successfully

---

## T161 — README

- [ ] product explanation
- [ ] architecture summary
- [ ] setup
- [ ] commands
- [ ] API
- [ ] DocsNary MCP
- [ ] testing
- [ ] screenshots/diagrams
- [ ] known limitations

---

## T162 — Architecture diagrams

- [ ] system architecture
- [ ] agent workflow
- [ ] runtime/interface architecture
- [ ] checkpoint/resume flow
- [ ] human review/commit boundary
- [ ] MCP boundary
- [ ] diagrams match implementation

---

## T163 — Final quality review

- [ ] no secrets
- [ ] no broken imports
- [ ] no dead endpoints
- [ ] no untested critical paths
- [ ] no false implementation claims
- [ ] documentation synchronized
- [ ] demo workflow verified

---

# Critical Path — Continue From Current State

The previous implementation has already completed the first four phases.

Therefore, the practical path forward is:

```text
COMPLETED
T001-T003
   ↓
T010-T012
   ↓
T020-T023
   ↓
T030-T033
   ↓
T040-T043
   ↓
CURRENT
T050 Evidence
   ↓
T051 Chunking
   ↓
T052 Embeddings
   ↓
T053 pgvector Retrieval
   ↓
T054 Context Builder
   ↓
T060 Conflicts
   ↓
T061-T063 Rules + Findings
   ↓
T070-T073 Human Review + Commit
   ↓
T080-T083 Async
   ↓
T090-T094 Incremental
   ↓
T100-T105 Simple Contract Domain
   ↓
T110-T113 DocsNary MCP
   ↓
T120-T125 Minimal UI
   ↓
T130-T133 Security
   ↓
T140-T144 Observability
   ↓
T150-T155 Tests
   ↓
T160-T163 Delivery
```

---

# Minimum Viable Task 1 Demo

If time becomes tight, this is the demo to protect:

```text
Contract
Amendment
Invoice
Renewal Notice
       ↓
   Upload
       ↓
  Agent Workflow
       ↓
Extract Facts
       ↓
Retrieve Evidence
       ↓
Detect Conflict
       ↓
Run User Rules
       ↓
Generate Findings
       ↓
Human Review
   ↙         ↘
Approve     Reject
   ↓
Commit Approved Changes
       ↓
Grounded Report
       ↓
New Amendment Arrives
       ↓
Incremental Update
       ↓
Affected Section Changes
Unaffected Section Preserved
       ↓
Same Workflow Driven via MCP
```

This is the vertical slice that demonstrates the core Task 1 requirements without spending time building a large business application.

---

# What NOT to Build in Task 1

Do NOT add these to this checklist:

- Win/Loss debrief
- Sales transcript analysis
- Quarterly competitive brief
- SuperDocs document workflow
- SuperDocs API integration
- SuperDocs MCP integration
- full contract-management product
- unnecessary UI polish
- unnecessary domain-specific features

Those belong to **Task 2** or are outside the assignment scope.

---

# Task Update Protocol

When implementing a task:

1. Change `[ ]` to `[~]` when work starts.
2. Implement the feature.
3. Add/update tests.
4. Run the relevant tests.
5. Change `[~]` to `[x]` only after verification.
6. Update `PROGRESS.md`.
7. Commit changes with the task ID.

Recommended commit format:

```text
feat(T050): add evidence model
feat(T053): add pgvector retrieval
feat(T060): add conflict detection
test(T153): add workflow recovery test
docs(T161): update README setup
```

If blocked:

```text
[!] T053 - BLOCKED
```

and record the reason in `PROGRESS.md`.

---

# Final Task 1 Completion Checklist

Before declaring Task 1 complete:

- [ ] Multi-document corpus works.
- [ ] Mixed document formats work.
- [ ] Agent has visible stages.
- [ ] Agent makes meaningful path decisions.
- [ ] Facts are structured.
- [ ] Important claims have evidence/citations.
- [ ] Conflicts are surfaced with evidence from both sides.
- [ ] User-provided rules can be supplied and executed.
- [ ] Source documents are checked against rules.
- [ ] Generated deliverable is checked against rules.
- [ ] Zero-findings case works.
- [ ] Findings are individually reviewable.
- [ ] Approve/reject is item-level.
- [ ] Only approved changes commit.
- [ ] Run resumes after process interruption.
- [ ] Concurrent runs are isolated.
- [ ] Incremental updates work.
- [ ] Unaffected output is preserved.
- [ ] Prompt injection is handled safely.
- [ ] Unsupported claims are rejected/flagged.
- [ ] DocsNary MCP can drive the complete workflow.
- [ ] Cost/time is visible.
- [ ] Resilience tests work without a live API key.
- [ ] Fresh clone works.
- [ ] README is complete.
- [ ] Architecture documentation is accurate.
- [ ] Final demo proves the complete Task 1 workflow.

---

# Definition of Task 1 Complete

Task 1 is complete when a reviewer can take the repository, follow the documented setup, provide a small set of related vendor/contract/invoice documents and a rule set, run the agentic workflow, observe its decisions, inspect evidence and conflicts, review proposed findings item-by-item, approve/reject them, obtain a grounded final report, interrupt and resume a run, add a new document for an incremental update, and drive the same workflow programmatically through **DocsNary's own MCP server**.

**Task 2 is intentionally excluded from this file.**
