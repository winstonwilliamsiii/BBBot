"""Demo/Testing main service for Demo_Bots database (port 3307)."""
from prediction_analytics.services.demo_polymarket import fetch_polymarket_contracts
from prediction_analytics.services.demo_kalshi import fetch_kalshi_contracts
from prediction_analytics.services.demo_probability import implied_probability, generate_rationale
from prediction_analytics.services.demo_sentiment import sentiment_score
from prediction_analytics.services.demo_db import insert_probability, insert_sentiment

def run_polymarket():
    """Fetch and process Polymarket contracts."""
    data = fetch_polymarket_contracts()

    for market in data.get("markets", []):
        contract_id = market["id"]
        bid = float(market["bestBid"])
        ask = float(market["bestAsk"])

        prob = implied_probability(bid, ask)
        rationale = generate_rationale(prob)

        insert_probability(contract_id, "Polymarket", prob, 0.85, rationale)

        # sentiment placeholder
        text = market.get("question", "")
        score, strength = sentiment_score(text)
        insert_sentiment(contract_id, score, strength, "Polymarket")

def run_kalshi():
    """Fetch and process Kalshi contracts."""
    data = fetch_kalshi_contracts()

    for market in data.get("markets", []):
        contract_id = market["id"]
        bid = float(market["best_bid"])
        ask = float(market["best_ask"])

        prob = implied_probability(bid, ask)
        rationale = generate_rationale(prob)

        insert_probability(contract_id, "Kalshi", prob, 0.90, rationale)

        text = market.get("title", "")
        score, strength = sentiment_score(text)
        insert_sentiment(contract_id, score, strength, "Kalshi")

if __name__ == "__main__":
    print("Running Demo_Bots prediction analytics (port 3307)...")
    run_polymarket()
    run_kalshi()
    print("Demo run complete!")
