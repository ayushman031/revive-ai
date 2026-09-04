"""Recovery action execution layer. Background workers process approved
RecoveryAction records. Enforces idempotency locks before calling external
providers. Only executes actions that have passed the deterministic policy
gate."""
