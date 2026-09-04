"""Deterministic policy gate. Evaluates candidate recovery recommendations
against merchant and system rules. Returns structured, auditable decisions.
The policy layer has veto authority over all ML recommendations. No LLM or
probabilistic logic is permitted in this module."""
