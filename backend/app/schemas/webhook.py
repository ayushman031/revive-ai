"""Schemas for incoming webhooks."""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class RazorpayWebhookEnvelope(BaseModel):
    """
    Minimal extraction of a Razorpay webhook payload.
    
    Tolerates arbitrary additional fields since we preserve the raw JSON
    and Razorpay payloads can evolve.
    """
    event: str = Field(..., description="The type of the Razorpay event (e.g. payment.failed)")
    
    model_config = ConfigDict(extra="allow")
