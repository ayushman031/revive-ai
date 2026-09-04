"""Schemas for service health checks."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Stable health endpoint response."""

    status: str
    service: str
