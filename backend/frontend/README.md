# Docsnary Frontend

A React + TypeScript + Vite single-page app for the Docsnary review
workflow: upload a document, run the analysis pipeline, review and
decide on findings, and read the committed case register.

## Setup

```bash
cd frontend
npm install
cp .env.example .env   # defaults to http://localhost:8000
npm run dev
```

Requires the backend running (see the backend's own setup guide) with
CORS already configured for `http://localhost:5173` (Vite's default
dev port — no backend changes needed for local development).

## Build

```bash
npm run build     # type-checks (tsc -b) then builds to dist/
npm run preview   # serve the production build locally
```

## Pages

| Route | Backend endpoints used | Purpose |
|---|---|---|
| `/` (Documents) | `GET/POST /documents`, `GET /documents/{id}/versions` | Upload a document, browse uploaded documents, jump to starting a run |
| `/runs` | `POST /runs`, `GET /runs/{run_id}` | Pick a document version + case ID, run the pipeline, see status/token usage/cost |
| `/findings` | `GET /findings`, `POST /findings/{id}/decide`, `POST /runs/{run_id}/finalize` | Approve/reject/edit each finding individually; commit approved findings |
| `/report` | `GET /cases/{case_id}/report` | The committed canonical register for a case |

The active case ID is shared across pages (sidebar field, persisted in
`localStorage`) since a real review session usually stays on one case
at a time — but every page also accepts an explicit ID via its own
form/URL param, so you can jump straight to a specific run or case
report from a link or bookmark.

## Design

A "case file / ledger" visual identity rather than a generic SaaS
dashboard, since this is an audit tool: paper-toned background, a
serif display face (Source Serif 4) for values and headings, a
monospace face (IBM Plex Mono) for evidence quotes, field names, and
IDs, and a rotated "stamp" badge as the one deliberately bold element
marking each finding's review status (pending / approved / rejected /
committed).

## What's not here

This covers the four screens described for Phase C. It intentionally
does not include: authentication/login (Phase D), a document
preview/viewer pane, real-time run status polling (status is
fetched on demand, not streamed), or drag-and-drop upload. All are
straightforward additions on top of the existing API client in
`src/lib/api.ts` if needed later.
