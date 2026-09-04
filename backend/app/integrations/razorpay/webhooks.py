"""Razorpay webhook signature verification."""

import hmac
import hashlib


def verify_webhook_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """
    Verify the authenticity of a Razorpay webhook payload.

    Args:
        payload_body: The raw bytes of the incoming request body.
        signature: The x-razorpay-signature header value.
        secret: The expected webhook secret.

    Returns:
        True if the signature is valid, False otherwise.
    """
    if not signature or not secret:
        return False

    try:
        # Reconstruct the expected signature using HMAC SHA-256
        expected_mac = hmac.new(
            key=secret.encode("utf-8"),
            msg=payload_body,
            digestmod=hashlib.sha256
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_mac, signature)
    except Exception:
        # Safely reject on any unexpected encoding or hashing errors
        return False
