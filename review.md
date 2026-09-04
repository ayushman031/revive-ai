# REVIVE — Technical Review & Problem Domain Analysis

## 1. Executive Summary & Problem Statement

### 1.1 The Industry Problem: Revenue Leakage in Digital Payments
Digital merchants and SaaS platforms lose **5% to 15% of their total transaction volume** to payment friction and failures:
- **Failed Immediate Payments & Gateway Glitches**: Transient network dropouts, temporary banking downtimes, and acquirer switch failures cause immediate drop-offs.
- **Failed Recurring & Subscription Payments (Dunning / Involuntary Churn)**: Insufficient balance at billing time, expired mandates, or temporary card limits lead to high customer churn.
- **Abandoned Checkouts**: Customers abandon transactions when friction occurs or when redirected without immediate alternatives.
- **Naive Retries Cause Friction & Penalties**: Blindly retrying failed transactions incurs gateway penalty fees, risks card-network fraud flagging, and annoys customers.
- **Lack of Verified Measurement**: Merchants rarely know whether an eventual payment was recovered because of an intervention or if the customer would have paid anyway (cannibalization / false attribution).

### 1.2 The AI Dilemma in Financial Workflows
While AI/ML can effectively predict recovery probabilities and choose optimal communication channels, **probabilistic AI must never directly execute financial actions or perform arithmetic**:
- Hallucinations or unbounded retries could charge customers multiple times or violate compliance.
- Non-deterministic logic makes auditing and compliance reporting impossible.

---

## 2. REVIVE Solution & Operating Philosophy

**REVIVE** is an AI-driven, policy-governed Revenue Recovery Agent tailored for the **Razorpay Buildathon (Track 03)**. 

REVIVE introduces an 8-stage, deterministic pipeline:

```
DETECT ➔ DIAGNOSE ➔ PREDICT ➔ DECIDE ➔ POLICY CHECK ➔ EXECUTE ➔ MEASURE ➔ AUDIT
```

### Core Recovery Workflow Stages

| Stage | Name | Role & Responsibility | Engine / Gate Type |
|---|---|---|---|
| 1 | **DETECT** | Ingest Razorpay webhooks (e.g. `payment.failed`, `order.paid`, `subscription.halted`) idempotently with signature verification. | Deterministic (FastAPI / Redis) |
| 2 | **DIAGNOSE** | Categorize failure reason (soft decline, hard decline, network timeout, insufficient funds, mandate failure). | Rule-based classifier |
| 3 | **PREDICT** | Calculate probability of recovery ($P_{\text{recovery}}$) across available intervention channels. | ML Model (XGBoost / scikit-learn) |
| 4 | **DECIDE** | Select the best intervention strategy (Expected Value Maximization: $E = P_{\text{rec}} \times \text{Amount} - \text{Cost}_{\text{int}}$). | Optimization Heuristic |
| 5 | **POLICY CHECK** | **Deterministic Safety Gate**: Enforce retry limits, cooling periods, customer fatigue limits, and merchant rules. Reject or override unsafe actions. | Deterministic Policy Gate (Zero LLM/ML discretion) |
| 6 | **EXECUTE** | Dispatch allowed action via Razorpay API (Smart Retry, Payment Link) or notification services. | Async Worker (Celery / Redis) |
| 7 | **MEASURE** | Track conversion, verify attribution with actual Razorpay settlement webhooks, and calculate net recovered revenue. | Ledger / SQL Analytics |
| 8 | **AUDIT** | Persist complete immutable trace: inputs, model version, scores, policy evaluation result, execution outcome, and timestamps. | PostgreSQL Audit Store |

---

## 3. Financial & Action Safety Invariants

REVIVE is built with non-negotiable safety rules:

1. **No LLM in Financial Math**: All currency calculations use exact decimal/integer representations (paisa / minor units), never floating-point arithmetic or LLM completions.
2. **Policy Gate is Absolute**: ML models can only *recommend*; deterministic code *authorizes*. If the policy gate rejects an action (e.g. max retries exceeded or user fatigued), the action is suppressed regardless of predicted recovery probability.
3. **Idempotency Everywhere**: Webhook event IDs (`event_id`, `payment_id`) are deduplicated at ingestion and execution boundaries to prevent duplicate charges or spam nudges.
4. **Attribution Integrity**: Expected recovery is strictly separated from verified recovered revenue. Revenue is counted as recovered only when confirmed by authenticated Razorpay settlement/payment webhooks.

---

## 4. Current Repository Architecture & State Review

### 4.1 Technology Stack
- **Backend**: Python 3.11+, FastAPI, Pydantic Settings, SQLAlchemy 2.0, Alembic
- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS
- **Data & Queue**: PostgreSQL 16 (Relational/Audit Store), Redis 7 (Caching & Message Broker)
- **Containerization**: Docker Compose (`compose.yaml`)
- **Testing**: Pytest for backend unit/integration tests

### 4.2 Implementation Audit (Phase 1 Status)

```
c:/revive/revive-ai/
├── AGENTS.md                  # Project constitution, safety rules, workflow constraints
├── README.md                  # Setup guide, run commands, architecture overview
├── compose.yaml               # Docker Compose orchestration (db, redis, backend, frontend)
├── .env.example               # Non-secret configuration template
├── backend/
│   ├── app/
│   │   ├── api/routes/health.py   # Health check endpoints (/health)
│   │   ├── core/
│   │   │   ├── config.py          # Pydantic BaseSettings management
│   │   │   └── database.py        # SQLAlchemy Base, Engine, and get_db session generator
│   │   ├── models/                # Reserved for SQLAlchemy domain models
│   │   ├── schemas/               # Reserved for Pydantic API schemas
│   │   └── services/              # Reserved for business logic & Razorpay integrations
│   ├── alembic/                   # Database migration environment
│   └── tests/                     # Pytest suite (health check & database lifecycle tests)
├── frontend/                  # Next.js App Router UI foundation
├── data/                      # Data storage for synthetic training datasets & feature stores
├── ml/                        # ML training notebooks, feature pipelines, and model artifacts
└── docs/                      # Technical documentation
```

### 4.3 Validation & Health
- **Database Lifecycle**: Verified with session generator unit tests ensuring session cleanup under normal and exception conditions.
- **Configuration**: Pydantic settings validate environment variables with safe defaults for local development.
- **Docker Orchestration**: Complete local multi-container environment configured for backend, frontend, postgres, and redis.

---

## 5. Candidate Interventions & Domain Vocabulary

| Intervention | Description | Policy Constraints |
|---|---|---|
| **Smart Retry** | Re-attempt payment at optimal hour based on historical gateway recovery windows. | Max 3 attempts; min 4h backoff; no retries on hard card declines. |
| **Payment Link** | Generate personalized Razorpay payment link (UPI, Netbanking, Cards) sent via SMS/Email. | Max 1 active link per failed order; configurable expiration window. |
| **Customer Nudge** | Contextual notification asking customer to update card or retry checkout. | Max 2 nudges per 24 hours to prevent fatigue. |
| **Human Escalation** | Route high-value B2B/Enterprise failed payments to merchant support team. | Triggered for transactions above configurable threshold (e.g. > ₹25,000). |
| **Suppress / No Action** | Intentionally take no action if fraud risk is high or recovery cost exceeds value. | Default fallback when policy rejects or expected value is negative. |

---

## 6. Implementation Roadmap & Next Phases

- [x] **Phase 1: Foundations & Architecture** (FastAPI, Next.js, Postgres, Redis, Pytest, Docker).
- [ ] **Phase 2: Data Models & Alembic Migrations** (Payment events, recovery sessions, policy logs, audit ledger).
- [ ] **Phase 3: Razorpay Webhook Ingestion & Deduplication** (Signature verification, idempotency key store, error classifier).
- [ ] **Phase 4: ML Prediction & Diagnostic Engine** (Synthetic training data, soft vs. hard decline diagnostics, recovery likelihood scorer).
- [ ] **Phase 5: Deterministic Policy Gate & Execution Engine** (Rule evaluator, rate limiters, Razorpay API execution client).
- [ ] **Phase 6: Merchant Dashboard & Real-Time Analytics** (Live recovery feed, ROI metrics, intervention timeline, policy overrides).
