# REVIVE

REVIVE is an AI Revenue Recovery Agent for Razorpay Buildathon Track 03. It identifies revenue at risk, diagnoses the cause, predicts recovery likelihood, recommends an intervention, enforces deterministic policy controls, executes only permitted actions, measures verified recovered revenue, and preserves a complete audit trail.

## Recovery workflow

```
DETECT → DIAGNOSE → PREDICT → DECIDE → POLICY CHECK → EXECUTE → MEASURE → AUDIT
```

## Architecture

- **Backend:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic
- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS
- **Data services:** PostgreSQL 16, Redis 7
- **Background jobs:** Celery with Redis broker
- **ML:** scikit-learn, XGBoost (future phases)
- **Payments:** Razorpay REST API and webhooks (future phases)
- **Tests:** Pytest (backend), Playwright (frontend, future phases)
- **Local environment:** Docker Compose

## Repository layout

```
backend/
  app/
    api/                    HTTP route handlers
    core/                   Configuration, database, Redis
    models/                 SQLAlchemy domain models (Phase 2+)
    schemas/                Pydantic request/response schemas
    repositories/           Database query and persistence layer
    services/               Business logic orchestration
    diagnostics/            Deterministic failure classifier
    ml/                     ML inference (read-only, no execution)
    policy/                 Deterministic policy gate
    execution/              Background action workers
    integrations/razorpay/  Razorpay API client and webhooks
    measurement/            Recovery attribution and verification
    audit/                  Immutable audit trail service
    main.py                 FastAPI application factory
  alembic/                  Database migration environment
  tests/                    Backend test suite
  requirements.txt          Python dependencies
  Dockerfile                Backend container image
  alembic.ini               Alembic configuration

frontend/                   Next.js application
data/                       Raw, processed, and generated datasets
ml/
  data/                     Training datasets
  training/                 Training scripts and pipelines
  inference/                Inference pipeline scripts
  models/                   Serialized model artifacts
  notebooks/                Exploratory notebooks
  tests/                    ML evaluation tests
docs/                       Project documentation
```

## Prerequisites

- Docker Desktop with Docker Compose v2
- Python 3.12 or later (for local backend development and tests)
- Node.js 20 or later and npm (for local frontend development)

## Quick start

1. Copy the example configuration:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Review the local-only values in `.env`. Do not commit that file.

3. Start all services:

   ```powershell
   docker compose up --build
   ```

4. Verify the backend is running:

   ```powershell
   curl http://localhost:8000/health
   # {"status":"ok","service":"revive-api"}
   ```

To stop, press `Ctrl+C`, then run `docker compose down`.

## Backend development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
cd backend
python -m pytest -v
```

Run the API server locally (with `.env` in the repository root):

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

## Frontend development

```powershell
cd frontend
npm install
npm run dev
```

## Service URLs

When Docker Compose is running:

| Service | URL |
|---|---|
| Backend health | http://localhost:8000/health |
| Backend API docs | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |

## Architectural safety rules

1. LLMs never perform financial calculations.
2. ML models never directly execute financial actions.
3. Every recovery action passes through a deterministic policy gate.
4. Monetary values use exact integer representations (paisa / minor units).
5. Prediction, recommendation, policy evaluation, execution, and measurement are strictly separated.
6. Policy decisions are structured and auditable.
7. No policy bypasses for demos, tests, jobs, retries, or internal tools.

## Current status

**Phase 1 — Project Scaffolding** is complete. The repository contains the foundational directory structure, health endpoint, configuration, Docker Compose services, and test infrastructure. No business logic, domain models, or external integrations are implemented.
