"""Deterministic Diagnosis Engine for failed payments."""

import re
from dataclasses import dataclass
from typing import Any

from app.models.constants import FailureCategory

RULE_VERSION = "2026.04.1"

# Sensitive patterns: 13-19 digit card PANs, 3-4 digit CVV/CVC, pin/passwords
PAN_REGEX = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
CVV_REGEX = re.compile(r"\b\d{3,4}\b")
SENSITIVE_KEY_NAMES = {"cvv", "cvc", "pan", "card_number", "pin", "password", "token", "secret"}


@dataclass(frozen=True)
class DiagnosisResult:
    failure_category: FailureCategory
    is_retryable: bool
    root_cause_summary: str
    confidence: float
    evidence: dict[str, Any]
    rule_version: str = RULE_VERSION


def redact_sensitive_text(text: str | None) -> str | None:
    """Redact PANs and sensitive sequences from diagnostic text strings."""
    if not text:
        return text
    # Redact PAN-like digit sequences
    redacted = PAN_REGEX.sub("[REDACTED_PAN]", text)
    return redacted


def sanitize_evidence_dict(raw_data: dict[str, Any]) -> dict[str, Any]:
    """Recursively scrub any sensitive field keys or values from evidence."""
    sanitized: dict[str, Any] = {}
    for k, v in raw_data.items():
        if any(sens in k.lower() for sens in SENSITIVE_KEY_NAMES):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_evidence_dict(v)
        elif isinstance(v, str):
            sanitized[k] = redact_sensitive_text(v)
        else:
            sanitized[k] = v
    return sanitized


class DiagnosisEngine:
    """
    Deterministic rule-based engine to classify payment failure signals.

    Canonical Rule Precedence:
    1. NETWORK_ERROR (timeout, network dropped, connection reset)
    2. GATEWAY_ERROR (Razorpay / acquirer internal service failure, downtime)
    3. AUTH_FAILED (OTP incorrect/expired, 3DS authentication failure)
    4. INSUFFICIENT_FUNDS (account balance insufficient)
    5. CARD_EXPIRED (card past validity date)
    6. BANK_DECLINE (general issuer decline / transaction not permitted)
    7. UNKNOWN (fallback when evidence is missing or ambiguous)
    """

    @classmethod
    def diagnose(
        cls,
        error_code: str | None = None,
        error_description: str | None = None,
        error_source: str | None = None,
        error_step: str | None = None,
        error_reason: str | None = None,
        method: str | None = None,
    ) -> DiagnosisResult:
        # Sanitize all incoming text fields
        code_clean = (error_code or "").strip().upper()
        desc_clean = (error_description or "").strip().lower()
        source_clean = (error_source or "").strip().lower()
        step_clean = (error_step or "").strip().lower()
        reason_clean = (error_reason or "").strip().lower()

        base_evidence = {
            "error_code": code_clean or None,
            "error_source": source_clean or None,
            "error_step": step_clean or None,
            "error_reason": reason_clean or None,
            "raw_description_preview": redact_sensitive_text(error_description[:100] if error_description else None),
            "payment_method": method,
        }

        # Rule 1: NETWORK_ERROR (Precedence 1)
        # Transient network issues, connection resets, gateway-to-bank timeouts
        network_indicators = [
            "timeout", "timed_out", "connection_reset", "network", "gateway_timeout",
            "connection_error", "request_timeout", "socket", "timed out"
        ]
        if (
            any(ind in code_clean.lower() for ind in network_indicators)
            or any(ind in reason_clean for ind in network_indicators)
            or any(ind in desc_clean for ind in network_indicators)
            or (source_clean in ("gateway", "bank") and ("timeout" in reason_clean or "timeout" in desc_clean))
        ):
            evidence = sanitize_evidence_dict({
                **base_evidence,
                "matched_rule": "RULE_1_NETWORK_TIMEOUT",
            })
            return DiagnosisResult(
                failure_category=FailureCategory.NETWORK_ERROR,
                is_retryable=True,
                root_cause_summary="Transient network or connection timeout between payment gateway and banking switch.",
                confidence=1.0,
                evidence=evidence,
            )

        # Rule 2: GATEWAY_ERROR (Precedence 2)
        # Razorpay/acquirer platform downtime, internal server error
        gateway_indicators = [
            "gateway_error", "internal_server_error", "service_unavailable",
            "acquirer_down", "system_error", "bank_unavailable"
        ]
        if (
            source_clean in ("gateway", "acquirer")
            and (
                "server_error" in code_clean.lower()
                or any(ind in code_clean.lower() for ind in gateway_indicators)
                or any(ind in reason_clean for ind in gateway_indicators)
                or any(ind in desc_clean for ind in gateway_indicators)
            )
        ) or "GATEWAY_ERROR" in code_clean:
            evidence = sanitize_evidence_dict({
                **base_evidence,
                "matched_rule": "RULE_2_GATEWAY_INTERNAL_ERROR",
            })
            return DiagnosisResult(
                failure_category=FailureCategory.GATEWAY_ERROR,
                is_retryable=True,
                root_cause_summary="Temporary gateway or acquirer service degradation.",
                confidence=0.95,
                evidence=evidence,
            )

        # Rule 3: AUTH_FAILED (Precedence 3)
        # OTP incorrect, expired, 3D Secure verification failed, user dropped auth
        auth_indicators = [
            "otp", "authentication", "3ds", "verification_failed", "auth_failed",
            "otp_incorrect", "otp_expired", "invalid_otp", "incorrect_otp"
        ]
        if (
            step_clean in ("otp", "auth", "authentication", "3ds")
            or any(ind in code_clean.lower() for ind in auth_indicators)
            or any(ind in reason_clean for ind in auth_indicators)
            or any(ind in desc_clean for ind in auth_indicators)
        ):
            evidence = sanitize_evidence_dict({
                **base_evidence,
                "matched_rule": "RULE_3_AUTHENTICATION_FAILURE",
            })
            return DiagnosisResult(
                failure_category=FailureCategory.AUTH_FAILED,
                is_retryable=False,  # Direct automated retry cannot pass OTP without customer interaction
                root_cause_summary="Customer authentication or OTP verification failed.",
                confidence=1.0,
                evidence=evidence,
            )

        # Rule 4: INSUFFICIENT_FUNDS (Precedence 4)
        funds_indicators = [
            "insufficient", "not_enough_funds", "low_balance", "balance",
            "insufficient_funds", "account_insufficient_balance"
        ]
        if (
            "INSUFFICIENT" in code_clean
            or any(ind in reason_clean for ind in funds_indicators)
            or any(ind in desc_clean for ind in funds_indicators)
        ):
            evidence = sanitize_evidence_dict({
                **base_evidence,
                "matched_rule": "RULE_4_INSUFFICIENT_FUNDS",
            })
            return DiagnosisResult(
                failure_category=FailureCategory.INSUFFICIENT_FUNDS,
                is_retryable=True,  # Smart retry can succeed after payday / replenishment
                root_cause_summary="Cardholder account balance or credit limit was insufficient.",
                confidence=1.0,
                evidence=evidence,
            )

        # Rule 5: CARD_EXPIRED (Precedence 5)
        expired_indicators = ["expired", "card_expired", "expiry_date"]
        if (
            "CARD_EXPIRED" in code_clean
            or any(ind in reason_clean for ind in expired_indicators)
            or any(ind in desc_clean for ind in expired_indicators)
        ):
            evidence = sanitize_evidence_dict({
                **base_evidence,
                "matched_rule": "RULE_5_CARD_EXPIRED",
            })
            return DiagnosisResult(
                failure_category=FailureCategory.CARD_EXPIRED,
                is_retryable=False,  # Expired card cannot succeed without new payment instrument
                root_cause_summary="Payment card has passed its expiration date.",
                confidence=1.0,
                evidence=evidence,
            )

        # Rule 6: BANK_DECLINE (Precedence 6)
        decline_indicators = [
            "declined", "payment_declined", "transaction_not_permitted",
            "do_not_honor", "restricted_card", "issuer_declined"
        ]
        if (
            source_clean == "bank"
            or any(ind in code_clean.lower() for ind in decline_indicators)
            or any(ind in reason_clean for ind in decline_indicators)
            or any(ind in desc_clean for ind in decline_indicators)
        ):
            evidence = sanitize_evidence_dict({
                **base_evidence,
                "matched_rule": "RULE_6_BANK_DECLINE",
            })
            return DiagnosisResult(
                failure_category=FailureCategory.BANK_DECLINE,
                is_retryable=False,
                root_cause_summary="Issuing bank declined transaction.",
                confidence=0.9,
                evidence=evidence,
            )

        # Rule 7: INVALID_PAYMENT_METHOD (Precedence 7)
        invalid_indicators = [
            "invalid_card", "invalid_payment_method", "not_supported",
            "unsupported_card", "invalid_method", "bad_request"
        ]
        if (
            "INVALID" in code_clean
            or any(ind in reason_clean for ind in invalid_indicators)
            or any(ind in desc_clean for ind in invalid_indicators)
        ):
            evidence = sanitize_evidence_dict({
                **base_evidence,
                "matched_rule": "RULE_7_INVALID_PAYMENT_METHOD",
            })
            return DiagnosisResult(
                failure_category=FailureCategory.INVALID_PAYMENT_METHOD,
                is_retryable=False,
                root_cause_summary="The payment method provided is invalid or unsupported.",
                confidence=0.9,
                evidence=evidence,
            )

        # Rule 8: ABANDONED_CHECKOUT (Precedence 8)
        abandoned_indicators = [
            "abandoned", "cancelled_by_user", "user_dropped", "cancelled"
        ]
        if (
            "ABANDONED" in code_clean
            or "CANCELLED" in code_clean
            or any(ind in reason_clean for ind in abandoned_indicators)
            or any(ind in desc_clean for ind in abandoned_indicators)
        ):
            evidence = sanitize_evidence_dict({
                **base_evidence,
                "matched_rule": "RULE_8_ABANDONED_CHECKOUT",
            })
            return DiagnosisResult(
                failure_category=FailureCategory.ABANDONED_CHECKOUT,
                is_retryable=True,  # Can retry by sending a payment link
                root_cause_summary="Customer abandoned the checkout or cancelled the payment.",
                confidence=0.9,
                evidence=evidence,
            )

        # Rule 9: UNKNOWN (Fallback)
        evidence = sanitize_evidence_dict({
            **base_evidence,
            "matched_rule": "RULE_FALLBACK_UNKNOWN",
        })
        return DiagnosisResult(
            failure_category=FailureCategory.UNKNOWN,
            is_retryable=False,
            root_cause_summary="Unrecognized payment failure reason; insufficient diagnostic evidence.",
            confidence=0.5,
            evidence=evidence,
        )
