#MAIN SERVICE
from services.polymarket_client import fetch_polymarket_contracts
from services.kalshi_client import fetch_kalshi_contracts
from services.probability_engine import implied_probability, generate_rationale
from services.sentiment_engine import sentiment_score
from services.db import insert_probability, insert_sentiment

def run_polymarket():
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
    run_polymarket()
    run_kalshi()