"""Test-only environment setup for the application factory."""

import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://revive:test@localhost:5432/revive_test"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
