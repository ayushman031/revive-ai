"""
Simulation configuration - explicitly labeled to separate from real production data.
"""

# SIMULATED INTERVENTION COSTS
# Note: These are SIMULATION ASSUMPTIONS, not verified Razorpay fees.
INTERVENTION_COSTS = {
    "retry": 0,
    "link": 10,
    "nudge": 2,
    "suppress": 0,
    "escalate": 50
}

# SIMULATED RECOVERY LATENCY
# Note: These are SIMULATED values in minutes, not observed production latency.
INTERVENTION_LATENCY_MINUTES = {
    "retry": 1,
    "link": 120,
    "nudge": 1440,
    "suppress": 0,
    "escalate": 2880
}
