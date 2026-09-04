"""Domain constants and enums."""

from enum import Enum


class ProcessingStatus(str, Enum):
    """Lifecycle states for asynchronous event processing."""
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class FailureCategory(str, Enum):
    """Canonical failure categories for deterministic diagnosis."""
    NETWORK_ERROR = "NETWORK_ERROR"
    GATEWAY_ERROR = "GATEWAY_ERROR"
    AUTH_FAILED = "AUTH_FAILED"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    CARD_EXPIRED = "CARD_EXPIRED"
    BANK_DECLINE = "BANK_DECLINE"
    ABANDONED_CHECKOUT = "ABANDONED_CHECKOUT"
    INVALID_PAYMENT_METHOD = "INVALID_PAYMENT_METHOD"
    UNKNOWN = "UNKNOWN"

