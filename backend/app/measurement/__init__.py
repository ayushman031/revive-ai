"""Recovery measurement and attribution layer. Compares inbound successful
payment events against active recovery cases to deterministically calculate
attribution and record verified recovered revenue. Strictly separates
expected recovery from verified, ledger-backed recovered revenue."""
