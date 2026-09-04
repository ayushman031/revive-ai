"""Health endpoint for service availability checks."""

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Report that the API process is available."""
    return HealthResponse(status="ok", service="revive-api")
