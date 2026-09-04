import logging
import uuid
from typing import Any, Protocol

logger = logging.getLogger(__name__)

class ProviderAdapter(Protocol):
    def execute(self, action_type: str, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        """Execute an intervention with the provider. Raises exception on failure."""
        ...


class MockRazorpayAdapter:
    """Deterministic Fake/Mock Provider Adapter for Phase 5 tests and local dev."""
    
    def execute(self, action_type: str, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        logger.info(f"Mock Provider executing {action_type} with idempotency_key={idempotency_key}")
        
        # Simulate provider failure for specific idempotency keys if needed in tests
        if "force_fail" in idempotency_key:
            raise Exception("Mock provider simulated failure")
            
        if "force_timeout" in idempotency_key:
            raise TimeoutError("Mock provider simulated timeout")

        return {
            "provider_reference": f"mock_{uuid.uuid4().hex[:8]}",
            "status": "success",
            "action_type": action_type,
            "idempotency_key_used": idempotency_key,
        }
