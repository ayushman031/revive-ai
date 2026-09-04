"""Razorpay integration layer. Handles HTTP client communication with
Razorpay REST APIs, webhook signature verification, authentication headers,
timeouts, and bounded retries. Credentials are sourced from environment
variables — never committed to source."""
