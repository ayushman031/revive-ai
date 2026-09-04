"""Deterministic Execution Boundary and State Machine for Phase 5."""

import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.recovery_action import RecoveryAction
from app.models.policy_decision import PolicyDecision
from app.providers.adapter import ProviderAdapter, MockRazorpayAdapter

logger = logging.getLogger(__name__)

class InvalidExecutionStateError(Exception):
    pass

class PolicyViolationError(Exception):
    pass


class ExecutionEngine:
    
    def __init__(self, session: Session, provider: ProviderAdapter | None = None):
        self.session = session
        self.provider = provider or MockRazorpayAdapter()

    def execute_action(self, action_id: uuid.UUID) -> bool:
        """
        Executes a RecoveryAction safely.
        State machine:
        1. Lock row and check if PENDING/APPROVED
        2. Transition to EXECUTING and COMMIT.
        3. Call external provider with idempotency_key.
        4. Transition to SUCCEEDED/FAILED and COMMIT.
        """
        
        # Step 1 & 2: Lock and transition to EXECUTING
        action = self.session.execute(
            select(RecoveryAction).where(RecoveryAction.id == action_id).with_for_update()
        ).scalar_one_or_none()

        if not action:
            logger.error(f"Action {action_id} not found.")
            return False

        if action.status not in ("PENDING", "APPROVED"):
            logger.warning(f"Action {action_id} is in invalid state {action.status} for execution.")
            # We do not crash celery if another worker already took it.
            return False

        # Verify Policy Gate
        policy = self.session.execute(
            select(PolicyDecision).where(PolicyDecision.id == action.policy_decision_id)
        ).scalar_one()

        if policy.decision != "ALLOW":
            raise PolicyViolationError(f"Cannot execute action {action_id}. Policy decision was {policy.decision}.")

        # Transition to EXECUTING
        action.status = "EXECUTING"
        action.executed_at = datetime.now(timezone.utc)
        idempotency_key = action.idempotency_key
        action_type = action.action_type
        payload = action.execution_payload or {}

        # Commit so other workers see EXECUTING
        self.session.commit()

        # Step 3: Provider Call
        try:
            response = self.provider.execute(
                action_type=action_type,
                payload=payload,
                idempotency_key=idempotency_key
            )
            final_status = "SUCCEEDED"
            error_message = None
        except Exception as e:
            logger.exception(f"Provider execution failed for {action_id}")
            response = None
            final_status = "FAILED"
            error_message = str(e)

        # Step 4: Persist final result
        action = self.session.execute(
            select(RecoveryAction).where(RecoveryAction.id == action_id)
        ).scalar_one()
        
        action.status = final_status
        action.execution_response = response
        action.error_message = error_message
        if response and "provider_reference" in response:
            action.external_reference_id = response["provider_reference"]
            
        self.session.commit()

        return final_status == "SUCCEEDED"
