"""Domain constants and enums."""

from enum import Enum


class ProcessingStatus(str, Enum):
    """Lifecycle states for asynchronous event processing."""
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
