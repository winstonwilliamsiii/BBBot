import pandas as pd
from fastapi.testclient import TestClient

import Main
import triton_bot
from triton_bot import TritonBot, TritonConfig


class _FakeTicker:
    def __init__(self, info):
        self.info = info


class _FakeYFinance:
    @staticmethod
    def download(*_args, **_kwargs):
        prices = [100 + i for i in range(120)]
        return pd.DataFrame({"Close": prices})

    @staticmethod
    def Ticker(_ticker):
        return _FakeTicker(
            {
                "sector": "Industrials",
                "industry": "Railroads",
                "forwardPE": 18.5,
                "revenueGrowth": 0.12,
                "profitMargins": 0.11,
                "beta": 1.03,
            }
        )


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
        return pd.DataFrame()

    @staticmethod
    def Ticker(_ticker):
        class _Ticker:
            info = {}

            @staticmethod
            def history(*_args, **_kwargs):
                return pd.DataFrame()

        return _Ticker()


class _FakeSentiment:
    def __init__(self, polarity):
        self.polarity = polarity


class _FakeTextBlob:
    def __init__(self, text):
        polarity = 0.45 if "demand" in text.lower() else -0.2
        self.sentiment = _FakeSentiment(polarity)


def _build_triton_bot() -> TritonBot:
    return TritonBot(
        TritonConfig(
            alpaca_api_key=None,
            alpaca_secret_key=None,
            alpaca_base_url="https://paper-api.alpaca.markets",
            ibkr_host="127.0.0.1",
            ibkr_port=7497,
            ibkr_client_id=7,
            fastapi_base_url="http://127.0.0.1:5001",
            mlflow_tracking_uri="http://localhost:5000",
            mlflow_experiment="Triton_Mansa_Transportation",
            enable_trading=False,
            enable_mlflow_logging=False,
            default_history_period="1y",
            default_history_interval="1d",
            forecast_steps=5,
            transport_universe=("IYT", "UNP", "CSX"),
            buy_threshold=0.18,
            sell_threshold=-0.18,
        )
    )


def test_triton_analysis_and_dry_run(monkeypatch):
    monkeypatch.setattr(triton_bot, "yf", _FakeYFinance)
    monkeypatch.setattr(triton_bot, "TextBlob", _FakeTextBlob)

    bot = _build_triton_bot()
    analysis = bot.analyze_ticker(
        "IYT",
        headlines=["Freight demand improved this quarter"],
    )

    assert analysis["ticker"] == "IYT"
    assert analysis["action"] in {"BUY", "HOLD", "SELL"}
    assert "composite_score" in analysis

    trade_action = analysis["action"] if analysis["action"] != "HOLD" else "BUY"
    order = bot.execute_trade(
        "alpaca",
        "IYT",
        trade_action,
        qty=5,
        dry_run=True,
    )
    assert order["status"] == "simulated"
    assert order["dry_run"] is True


def test_triton_fastapi_routes(monkeypatch):
    monkeypatch.setattr(triton_bot, "yf", _FakeYFinance)
    monkeypatch.setattr(triton_bot, "TextBlob", _FakeTextBlob)

    bot = _build_triton_bot()

    monkeypatch.setattr(Main, "get_triton_bot", lambda: bot)
    monkeypatch.setattr(Main, "TritonBot", TritonBot)

    client = TestClient(Main.app)

    status_response = client.get("/triton/status")
    assert status_response.status_code == 200
    assert status_response.json()["name"] == "Triton"

    health_response = client.get("/triton/health")
    assert health_response.status_code == 200
    assert "dependencies" in health_response.json()

    analyze_response = client.post(
        "/triton/analyze",
        json={
            "ticker": "IYT",
            "news_headlines": ["Transport demand remains strong"],
        },
    )
    assert analyze_response.status_code == 200
    assert "composite_score" in analyze_response.json()

    trade_response = client.post(
        "/triton/trade",
        json={
            "broker": "alpaca",
            "ticker": "IYT",
            "action": "BUY",
            "qty": 3,
            "dry_run": True,
        },
    )
    assert trade_response.status_code == 200
    assert trade_response.json()["status"] == "simulated"


def test_triton_alpha_vantage_price_fallback(monkeypatch):
    monkeypatch.setattr(triton_bot, "yf", _EmptyYFinance)
    monkeypatch.setattr(triton_bot, "TextBlob", _FakeTextBlob)
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "test-key")

    daily_payload = {
        "Time Series (Daily)": {
            f"2026-01-{day:02d}": {
                "1. open": str(100 + day),
                "2. high": str(101 + day),
                "3. low": str(99 + day),
                "4. close": str(100.5 + day),
                "5. adjusted close": str(100.5 + day),
                "6. volume": str(100000 + day),
            }
            for day in range(1, 40)
        }
    }
    overview_payload = {
        "Symbol": "IYT",
        "Sector": "Industrials",
        "Industry": "Transportation",
        "MarketCapitalization": "1000000000",
        "ForwardPE": "18.3",
        "QuarterlyRevenueGrowthYOY": "0.11",
        "ProfitMargin": "0.09",
        "Beta": "1.02",
    }

    def _fake_get(_url, params=None, timeout=10):
        if params and params.get("function") == "OVERVIEW":
            return _FakeResponse(overview_payload)
        return _FakeResponse(daily_payload)

    monkeypatch.setattr(triton_bot.requests, "get", _fake_get)

    bot = _build_triton_bot()
    analysis = bot.analyze_ticker("IYT", headlines=["Freight demand improved"])

    assert analysis["ticker"] == "IYT"
    assert analysis["technical"]["close"] is not None
    assert analysis["fundamental"]["forward_pe"] == 18.3
