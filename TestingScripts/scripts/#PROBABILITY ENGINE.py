#PROBABILITY ENGINE
def implied_probability(bid, ask):
    mid = (bid + ask) / 2
    return round(mid * 100, 2)

def generate_rationale(prob):
    if prob > 70:
        return "High confidence based on market pricing."
    if prob > 50:
        return "Moderate confidence with upward momentum."
    return "Low confidence; market uncertain."