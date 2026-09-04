# REVIVE Repository Guide

## Scope and delivery

REVIVE is an AI Revenue Recovery Agent for Razorpay Buildathon Track 03. Its
purpose is to identify revenue at risk, diagnose why it is at risk, estimate
the chance of recovery, choose an intervention, enforce policy, execute only
permitted actions, and measure the revenue actually recovered.

The required workflow is:

`DETECT → DIAGNOSE → PREDICT → DECIDE → POLICY CHECK → EXECUTE → MEASURE → AUDIT`

Implement the repository incrementally. Do not create application code, future
phases, integrations, or infrastructure unless the user explicitly asks for
that work. If a requirement leaves a critical business rule unclear, stop and
ask instead of inventing behavior. Explain before proposing a change to the
product architecture or business rules.

## Intended architecture

- Frontend: Next.js with TypeScript
- Backend: Python with FastAPI
- Database: PostgreSQL via SQLAlchemy
- Schema migrations: Alembic
- ML: Python, scikit-learn, and XGBoost
- Cache and background jobs: Redis and Celery
- Payments: Razorpay REST API and webhooks
- Tests: Pytest for backend; Playwright for frontend
- Local containers: Docker Compose

Prefer a simple, maintainable modular application over premature microservices.

## Financial and action safety

1. Never use an LLM for deterministic financial calculations.
2. Never permit an LLM or ML model to directly execute a financial action.
3. All recovery actions must flow through a deterministic policy gate before
   execution.
4. Make financial calculations reproducible, explicit, and independently
   testable. Use precise money representations suitable for currency values;
   do not rely on floating-point arithmetic for monetary totals.
5. Keep prediction, recommendation, policy evaluation, and action execution
   separate. Models may score or recommend; deterministic application code
   decides whether an action is allowed and performs it.
6. Make policy evaluation return a structured, persisted result that identifies
   the evaluated rules, inputs, decision, and rejection reasons.
7. Do not bypass the policy gate for internal tools, jobs, retries, tests, or
   demo flows.

## Recovery domain

Initial scenarios are:

- Failed payments
- Temporary gateway failures
- Abandoned checkout
- Failed recurring or subscription payments

Candidate interventions are:

- Smart retry
- Payment link
- Customer nudge
- Human escalation
- Suppress / no action

Treat these as product vocabulary, not automatic authorization to perform a
payment operation. Explicit, deterministic policy rules must govern each
execution attempt.

## Data, ML, and auditability

- Do not hardcode dashboard metrics that should be calculated from database
  records.
- Design synthetic datasets with realistic temporal and behavioral correlations;
  do not generate independent random fields that imply unrealistic behavior.
- Split train, validation, and test data chronologically to reduce temporal
  leakage. Never shuffle across the time boundary when evaluating predictive
  performance.
- Persist enough structured information for every AI recommendation to audit it:
  source signals, model and feature version, probabilities, expected recovery,
  selected intervention, policy result, and timestamps.
- Distinguish a recommendation or expected recovery from an actually executed
  action and from verified recovered revenue. Measurement must be traceable to
  supporting payment and webhook events.
- Version models, feature definitions, and policy configurations when they are
  introduced. Avoid opaque, unversioned decision logic.

## Razorpay and webhook rules

- Keep Razorpay credentials in environment variables; never commit secrets,
  keys, tokens, webhook secrets, or production identifiers.
- Verify webhook signatures before accepting or acting on an event.
- Process webhooks idempotently. Store and deduplicate an appropriate event
  identity, and make duplicate delivery safe at every downstream side effect.
- Record relevant raw event metadata and processing outcomes needed for audit,
  while minimizing stored sensitive data.
- Treat external API calls as fallible: use bounded retries where appropriate,
  clear error handling, and idempotency protections before a recovery action is
  sent.

## Engineering practices

- Use environment variables for credentials and deployment-specific
  configuration; provide non-secret example configuration only when requested.
- Write tests alongside important business logic, especially money handling,
  policy gates, webhook verification and idempotency, state transitions, and
  recovery measurement.
- Keep API schemas, domain rules, persistence models, and side-effecting
  integrations clearly separated as the implementation grows.
- Favor readable types, explicit validation, predictable error paths, and
  small modules with single responsibilities.
- Do not expose customer data, credentials, raw payment details, or sensitive
  operational data in logs, test fixtures, screenshots, or documentation.
- Before adding dependencies or services, verify that they are needed by the
  current requested phase.

## Change discipline

- Keep changes scoped to the explicitly requested phase.
- Preserve existing user work and do not overwrite unrelated changes.
- State assumptions that affect product behavior, financial outcomes, or data
  interpretation.
- Verify relevant tests and checks after implementation work, and report what
  was run and what remains unverified.
