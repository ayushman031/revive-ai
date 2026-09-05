# REVIVE — AI Revenue Recovery Agent

An AI-powered revenue recovery system that diagnoses failed payments, predicts recovery actions, applies deterministic policy guardrails, executes interventions, measures recovered revenue, and evaluates its performance against a baseline.

## Core capabilities implemented

- Webhook ingestion and idempotency
- Payment failure diagnosis
- ML-based recovery prediction
- Deterministic policy governance
- Recovery execution pipeline
- Measurement and revenue attribution
- Merchant operations dashboard
- Cases and case-detail views
- Analytics dashboard
- Evaluation dashboard
- Baseline vs REVIVE evaluation using 10,000 synthetic transactions

## Architecture

```text
Payment Webhook
     ↓
Diagnosis
     ↓
ML Prediction
     ↓
Policy Engine
     ↓
Execution
     ↓
Measurement
     ↓
Dashboard / Analytics / Evaluation
```

## Technology stack

**Backend:**
- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Celery
- Redis

**ML:**
- scikit-learn
- deterministic feature schema
- trained model artifacts

**Frontend:**
- Next.js
- React
- TypeScript
- Tailwind CSS
- Recharts

**Infrastructure:**
- Docker
- Docker Compose

## Phase progression

- **Phase 1** — Project foundation
- **Phase 2** — Domain/data model
- **Phase 3** — Webhook ingestion and idempotency
- **Phase 4** — Diagnosis and ML prediction
- **Phase 5** — Policy and execution
- **Phase 6** — Measurement + merchant dashboard
- **Phase 7** — Evaluation framework + Evaluation Dashboard (Current completed/frozen phase)

## Phase 7 evaluation result

> **IMPORTANT:** The following are results from the deterministic synthetic evaluation environment, NOT live production performance.

**Dataset:**
- 10,000 transactions
- Revenue at Risk: INR 80,434,154

**Baseline:**
- Recovery Rate: 21.80%
- Recovered Revenue: INR 17,537,381
- Net Recovered Revenue: INR 17,537,381

**REVIVE:**
- Recovery Rate: 22.49%
- Recovered Revenue: INR 18,093,020
- Net Recovered Revenue: INR 18,092,977.70

**Delta:**
- Recovery Rate: +0.69 percentage points
- Net Recovered Revenue: +INR 555,596.70
- Unnecessary Intervention Rate: -3.26 percentage points

## Evaluation assumptions

- **Intervention Costs:**
  - retry = INR 0
  - link = INR 10
  - nudge = INR 2
- **Simulated Recovery Latency:**
  - retry = 1 minute
  - link = 120 minutes
  - nudge = 1440 minutes
- *Latency is simulated and not observed production latency.*
- *Evaluation uses synthetic data.*

## How to run

**1. Start infrastructure and services:**
```powershell
docker compose up --build -d
```

**2. Run backend tests:**
```powershell
cd backend
uv run pytest tests/ -q
```

**3. Run frontend build:**
```powershell
cd frontend
npm install
npm run build
```

**4. Run evaluation simulator:**
```powershell
cd backend
uv run python scripts/run_evaluation.py
```

## Demo routes

When the frontend is running (e.g., via `npm run dev` or mapped via Docker on `http://localhost:3000` or `http://localhost:3001` depending on your environment):
- `/` (Overview)
- `/cases`
- `/analytics`
- `/evaluation`

## Repository status

**Phase 7 Step 3 is frozen at: v0.9.0**
