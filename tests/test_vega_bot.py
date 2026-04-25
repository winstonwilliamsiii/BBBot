import vega_bot
from fastapi.testclient import TestClient


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _EmptyYFinance:
    @staticmethod
    def download(*_args, **_kwargs):
        class _Empty:
            empty = True

        return _Empty()

    @staticmethod
    def Ticker(_ticker):
        class _Ticker:
            info = {}
            fast_info = {}

            @staticmethod
            def history(*_args, **_kwargs):
                class _Empty:
                    empty = True

                return _Empty()

        return _Ticker()


def test_vega_signal_alpha_vantage_fallback(monkeypatch):
    monkeypatch.setattr(vega_bot, "yf", _EmptyYFinance)
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "test-key")

    daily_payload = {
        "Time Series (Daily)": {
            f"2026-02-{day:02d}": {
                "1. open": str(100 + day),
                "2. high": str(101 + day),
                "3. low": str(99 + day),
                "4. close": str(100.5 + day),
                "5. adjusted close": str(100.5 + day),
                "6. volume": str(100000 + day),
            }
            for day in range(1, 29)
        }
    }
    overview_payload = {
        "Symbol": "WMT",
        "Name": "Walmart Inc.",
        "Sector": "Consumer Defensive",
        "Industry": "Discount Stores",
        "MarketCapitalization": "500000000000",
        "ForwardPE": "24.1",
        "ProfitMargin": "0.025",
        "ReturnOnEquityTTM": "0.20",
        "Beta": "0.55",
    }

    def _fake_get(_url, params=None, timeout=10):
        if params and params.get("function") == "OVERVIEW":
            return _FakeResponse(overview_payload)
        return _FakeResponse(daily_payload)

    monkeypatch.setattr(vega_bot.requests, "get", _fake_get)

    client = TestClient(vega_bot.app)
    response = client.post(
        "/signal",
        json={"ticker": "WMT", "timeframe": "1d", "direction": "auto", "news_headlines": []},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ticker"] == "WMT"
    assert "decision" in body
    assert body["fundamentals"]["data_source"] in {
        "alpha_vantage_overview",
        "ticker_info",
        "fast_info_fallback",
    }
