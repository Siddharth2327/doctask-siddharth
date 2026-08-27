# DOCSNARY Setup & Run Guide

## 1. Project Overview

DOCSNARY is a document-processing application that extracts structured information from documents, applies rules, generates findings for review, and commits approved findings into a case record.

The repository is organized as follows:

```text
docsnary/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── agents/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── db/
│   │   ├── integrations/
│   │   ├── mcp/
│   │   └── core/
│   ├── frontend/
│   ├── tests/
│   ├── alembic/
│   ├── scripts/
│   ├── requirements.txt
│   └── .env.example
├── prompts/
├── diagrams/
├── docs/
├── ARCHITECTURE.md
├── TASK.md
├── PROGRESS.md
└── IMPLEMENTATION.md
```

---

## 2. Prerequisites

Install the following before setting up DOCSNARY:

- Python 3.12 or newer
- Docker
- Docker Compose
- Node.js 20 or newer
- npm
- Git
- Tesseract OCR, if scanned documents need OCR processing

Verify the main tools:

```bash
python --version
docker --version
docker compose version
node --version
npm --version
```

On Windows, use PowerShell or another terminal that supports the commands above.

---

## 3. Clone the Repository

Clone the repository and move into the project directory:

```bash
git clone <repository-url>
cd docsnary
```

Replace `<repository-url>` with the actual Git repository URL.

---

## 4. Start Infrastructure

From the directory containing `docker-compose.yml`, start the required infrastructure services:

```bash
docker compose up -d
```

Check that the containers are running:

```bash
docker compose ps
```

If a service is not running, inspect its logs:

```bash
docker compose logs <service-name>
```

To stop the infrastructure later:

```bash
docker compose down
```

---

## 5. Create the Python Virtual Environment

Move into the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

### Windows PowerShell

Activate the environment:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, use an appropriate execution-policy setting for your local development environment.

### Linux/macOS

```bash
source .venv/bin/activate
```

Once activated, your terminal should indicate that the `.venv` environment is active.

---

## 6. Install Backend Dependencies

Upgrade pip:

```bash
pip install --upgrade pip
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

---

## 7. Configure Environment Variables

Create the local environment file from the example:

```bash
cp .env.example .env
```

On Windows PowerShell, if `cp` is unavailable:

```powershell
Copy-Item .env.example .env
```

### Deterministic AI Provider

For local development and demonstrations without a paid AI API key, configure:

```env
AI_PROVIDER=deterministic
```

This allows the application and tests to run without requiring a paid AI provider.

### Important

Never commit a real API key or other secrets to Git.

Keep secrets in `.env` or the appropriate local/secret-management system.

---

## 8. Run Database Migrations

Make sure you are inside the `backend` directory and that the virtual environment is active.

Run:

```bash
alembic upgrade head
```

This applies all database migrations required by the current version of DOCSNARY.

If migrations fail, verify that:

1. Docker infrastructure is running.
2. The database configuration in `.env` is correct.
3. You are running the command from the `backend` directory.
4. The virtual environment is active.

---

## 9. Start the Backend

From the `backend` directory:

```bash
uvicorn app.main:app --reload --port 8000
```

The backend should be available at:

```text
http://localhost:8000
```

FastAPI's interactive API documentation is available at:

```text
http://localhost:8000/docs
```

The API documentation is particularly useful for testing endpoints during development and demonstrations.

To stop the development server, press:

```text
Ctrl+C
```

---

## 10. Start the Frontend

Keep the backend running and open another terminal.

Move to the frontend directory:

```bash
cd backend/frontend
```

Install frontend dependencies:

```bash
npm install
```

Start the frontend development server:

```bash
npm run dev
```

The frontend normally runs at:

```text
http://localhost:5173
```

Open that address in a browser.

---

## 11. Recommended Terminal Setup

For local development, use separate terminals.

### Terminal 1: Infrastructure

From the repository root:

```bash
docker compose up -d
```

### Terminal 2: Backend

```bash
cd docsnary/backend
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Then:

```bash
uvicorn app.main:app --reload --port 8000
```

### Terminal 3: Frontend

```bash
cd docsnary/backend/frontend
npm run dev
```

This keeps Docker, the backend, and the frontend running independently.

---

## 12. Run the Test Suite

From the `backend` directory, with the virtual environment activated:

```bash
pytest -v
```

The test suite is designed to run without a paid AI API key when the deterministic provider is configured.

The tests cover important application behavior, including:

- Workflow execution
- Structured extraction
- Rules
- Review
- Commit behavior
- Idempotency
- Resilience
- Deterministic-provider behavior

A successful test run should report that all tests pass.

---

## 13. Basic DOCSNARY Demonstration Flow

The following flow can be used to demonstrate the application from document upload through case reporting.

### Step 1: Prepare a Document

Use a synthetic vendor contract or another suitable test document.

For example, the document can contain:

```text
Vendor: Acme Supplies
Contract Value: 100000
Start Date: 2026-01-01
End Date: 2026-12-31
Status: Active
```

### Step 2: Upload the Document

Upload the document through the DOCSNARY API or frontend.

### Step 3: Create a Run

Create a processing run and associate it with a case ID.

### Step 4: Run the Pipeline

Start the document-processing workflow.

The pipeline processes the document and produces structured information and findings.

### Step 5: Review Findings

Open the generated findings.

Review each finding individually.

### Step 6: Approve or Reject Findings

Approve valid findings and reject findings that should not be committed.

### Step 7: Commit Approved Findings

Commit the approved findings to the case.

### Step 8: View the Case Report

Open the resulting case report and verify that the approved information has been incorporated.

### Step 9: Test Incremental Processing

Upload a later document version to the same case.

Use this to demonstrate:

- Incremental changes
- New findings
- Contradictions
- Version-aware processing

---

## 14. Example Structured Result

A successful extraction can produce structured data similar to:

```text
vendor          = Acme Supplies
contract_value  = 100000
start_date      = 2026-01-01
end_date        = 2026-12-31
status          = Active
```

The exact output depends on the document, configured rules, and processing workflow.

---

## 15. Typical Startup Sequence

For a fresh local session, the recommended sequence is:

### 1. Start Docker

```bash
docker compose up -d
```

### 2. Enter the backend

```bash
cd backend
```

### 3. Activate the virtual environment

Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 4. Verify environment configuration

Make sure `.env` exists and contains the required local configuration.

For key-free local development:

```env
AI_PROVIDER=deterministic
```

### 5. Apply migrations

```bash
alembic upgrade head
```

### 6. Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

### 7. Start the frontend in a second terminal

```bash
cd backend/frontend
npm install
npm run dev
```

### 8. Verify

Open:

```text
Backend:  http://localhost:8000
API Docs: http://localhost:8000/docs
Frontend: http://localhost:5173
```

---

## 16. Troubleshooting

### Python is not recognized

Verify that Python 3.12+ is installed and available on your PATH:

```bash
python --version
```

On some Windows installations, the Python launcher may be available as:

```powershell
py --version
```

### Virtual environment activation fails on Windows

Try activating it from PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell reports an execution-policy error, configure the execution policy appropriate for your development machine and then retry.

### Docker services are not running

Check:

```bash
docker compose ps
```

Then inspect logs:

```bash
docker compose logs
```

### Database migration fails

Check:

```bash
docker compose ps
```

Then verify the database-related values in `.env`.

Retry:

```bash
alembic upgrade head
```

### Backend will not start

Verify that:

- The virtual environment is active.
- Dependencies are installed.
- `.env` exists.
- Infrastructure is running.
- You are inside the `backend` directory.

Then run:

```bash
uvicorn app.main:app --reload --port 8000
```

### Frontend will not start

From `backend/frontend`:

```bash
npm install
npm run dev
```

If dependencies are corrupted, remove the local dependency installation and reinstall:

```bash
rm -rf node_modules
npm install
```

On Windows PowerShell:

```powershell
Remove-Item -Recurse -Force node_modules
npm install
```

### Tests fail because of environment configuration

Make sure the deterministic provider is configured:

```env
AI_PROVIDER=deterministic
```

Then run:

```bash
pytest -v
```

---

## 17. Stopping DOCSNARY

Stop the backend and frontend development servers with:

```text
Ctrl+C
```

Stop Docker infrastructure from the repository root:

```bash
docker compose down
```

To remove the containers and associated volumes, use the appropriate Docker Compose cleanup command only when you intentionally want to reset local persisted infrastructure data.

---

## 18. Quick Reference

| Component | Command | Default Address |
|---|---|---|
| Infrastructure | `docker compose up -d` | Depends on service |
| Backend | `uvicorn app.main:app --reload --port 8000` | `http://localhost:8000` |
| API Docs | Backend-provided | `http://localhost:8000/docs` |
| Frontend | `npm run dev` | `http://localhost:5173` |
| Migrations | `alembic upgrade head` | N/A |
| Tests | `pytest -v` | N/A |

---

## 19. Final Verification Checklist

Before considering the local setup complete:

- [ ] Python 3.12+ is installed.
- [ ] Docker is installed and running.
- [ ] Docker Compose is available.
- [ ] Node.js 20+ and npm are installed.
- [ ] Tesseract is installed if OCR is required.
- [ ] Repository has been cloned.
- [ ] Docker infrastructure is running.
- [ ] Python virtual environment has been created.
- [ ] Python dependencies have been installed.
- [ ] `.env` has been created from `.env.example`.
- [ ] `AI_PROVIDER=deterministic` is configured for key-free local development.
- [ ] Database migrations have been applied.
- [ ] Backend starts successfully on port 8000.
- [ ] FastAPI documentation opens successfully.
- [ ] Frontend dependencies are installed.
- [ ] Frontend starts successfully on port 5173.
- [ ] Test suite passes with `pytest -v`.
- [ ] A sample document can be processed through the basic demonstration flow.

---

## 20. Development Notes

DOCSNARY contains both backend and frontend components, while the repository also includes architecture, task, progress, implementation, prompt, documentation, and diagram resources.

For implementation work, keep the following files aligned:

- `ARCHITECTURE.md` - intended system architecture
- `TASK.md` - implementation requirements and checklist
- `PROGRESS.md` - current implementation status
- `IMPLEMENTATION_GUIDE.md` - implementation guidance and details

When making changes, verify the relevant tests and update project documentation when behavior or setup requirements change.

Never commit local secrets, API keys, passwords, or other credentials.
