"""Tests for Phase 2 database models and metadata registration."""

import pytest
from sqlalchemy import MetaData
from sqlalchemy.schema import CreateTable

from app.core.database import Base
from app.models import (
    Merchant,
    Customer,
    Payment,
    PaymentAttempt,
    WebhookEvent,
    RecoveryCase,
    Diagnosis,
    Prediction,
    Recommendation,
    PolicyDecision,
    RecoveryAction,
    RecoveryMeasurement,
    AuditLog,
)


def test_metadata_contains_all_models() -> None:
    """Verify all 13 models are registered with the declarative Base."""
    tables = Base.metadata.tables.keys()
    assert "merchants" in tables
    assert "customers" in tables
    assert "payments" in tables
    assert "payment_attempts" in tables
    assert "webhook_events" in tables
    assert "recovery_cases" in tables
    assert "diagnoses" in tables
    assert "predictions" in tables
    assert "recommendations" in tables
    assert "policy_decisions" in tables
    assert "recovery_actions" in tables
    assert "recovery_measurements" in tables
    assert "audit_logs" in tables
    assert len(tables) >= 13


def test_table_creation_sqls() -> None:
    """Verify that SQLAlchemy can generate CREATE TABLE statements for all models
    without raising relationship or constraint errors."""
    from sqlalchemy.dialects import postgresql
    
    # We just need to iterate over all tables and compile them.
    # If there are ambiguous relationships or missing FKs, it will raise an error.
    for table_name, table in Base.metadata.tables.items():
        create_stmt = CreateTable(table).compile(dialect=postgresql.dialect())
        assert str(create_stmt).strip() != ""


def test_merchant_columns() -> None:
    """Verify Merchant columns and constraints."""
    table = Merchant.__table__
    assert table.c.razorpay_account_id.unique
    assert table.c.id.server_default is not None


def test_customer_constraints() -> None:
    """Verify Customer unique constraint."""
    table = Customer.__table__
    constraints = [c.name for c in table.constraints if c.name == "uq_merchant_razorpay_customer"]
    assert len(constraints) == 1


def test_payment_constraints() -> None:
    """Verify Payment columns and check constraint."""
    table = Payment.__table__
    assert str(table.c.amount.type) == "BIGINT"
    constraints = [c.name for c in table.constraints if c.name == "chk_payment_amount_positive"]
    assert len(constraints) == 1


def test_prediction_constraints() -> None:
    """Verify Prediction columns and check constraints."""
    table = Prediction.__table__
    assert str(table.c.risk_score.type) == "NUMERIC(5, 4)"
    assert str(table.c.features_snapshot.type) == "JSONB"
    constraints = [c.name for c in table.constraints if c.name == "chk_pred_risk_score_range"]
    assert len(constraints) == 1
    constraints = [c.name for c in table.constraints if c.name == "chk_pred_prob_retry_range"]
    assert len(constraints) == 1


def test_recovery_action_columns() -> None:
    """Verify RecoveryAction columns."""
    table = RecoveryAction.__table__
    assert table.c.idempotency_key.unique


def test_recovery_measurement_columns() -> None:
    """Verify nullable resolving foreign keys in RecoveryMeasurement."""
    table = RecoveryMeasurement.__table__
    assert table.c.resolution_attempt_id.nullable
    assert table.c.resolution_webhook_event_id.nullable


def test_audit_log_columns() -> None:
    """Verify AuditLog columns."""
    table = AuditLog.__table__
    assert str(table.c.details.type) == "JSONB"
    assert table.c.merchant_id.nullable
