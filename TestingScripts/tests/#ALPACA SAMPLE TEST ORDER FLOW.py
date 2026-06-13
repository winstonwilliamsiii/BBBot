#ALPACA SAMPLE TEST ORDER FLOW
# tests/test_alpaca_orders.py
import os
import pytest
from alpaca_trade_api import REST

@pytest.fixture
def alpaca_client():
    key_id = os.getenv("APCA_API_KEY_ID")
    secret_key = os.getenv("APCA_API_SECRET_KEY")
    base_url = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")
    return REST(key_id, secret_key, base_url)

def test_place_and_cancel_order(alpaca_client):
    try:
        # Place a small paper trade
        order = alpaca_client.submit_order(
            symbol="AAPL",
            qty=1,
            side="buy",
            type="market",
            time_in_force="gtc"
        )
        assert order is not None
        assert order.symbol == "AAPL"

        # Cancel the order
        alpaca_client.cancel_order(order.id)
    except Exception as e:
        pytest.fail(f"Alpaca API error: {e}")

