"""Simplified probability engine for Demo_Bots testing."""

def implied_probability(bid, ask):
    """Calculate implied probability from bid/ask midpoint."""
    mid = (bid + ask) / 2
    return round(mid * 100, 2)

def generate_rationale(prob):
    """Generate simple rationale based on probability threshold."""
    if prob > 70:
        return "High confidence based on market pricing."
    if prob > 50:
        return "Moderate confidence with upward momentum."
    return "Low confidence; market uncertain."
