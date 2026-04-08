import pandas as pd
from fastapi.testclient import TestClient

import Main
import hydra_bot
from hydra_bot import HydraBot, HydraConfig


class _FakeTicker:
    def __init__(self, info):
        self.info = info


class _FakeYFinance:
    @staticmethod
    def download(*args, **kwargs):
        prices = [
            100,
            101,
            102,
            103,
            104,
            105,
            106,
            107,
            108,
            109,
            110,
            111,
            112,
            113,
            114,
            115,
            116,
            117,
            118,
            119,
            120,
            121,
            122,
            123,
            124,
            125,
            126,
            127,
            128,
            129,
            130,
            131,
            132,
            133,
            134,
            135,
            136,
            137,
            138,
            139,
            140,
            141,
            142,
            143,
            144,
            145,
            146,
            147,
            148,
            149,
            150,
            151,
            152,
            153,
            154,
            155,
            156,
            157,
            158,
            159,
            160,
            161,
            162,
            163,
            164,
            165,
            166,
            167,
            168,
            169,
            170,
            171,
            172,
            173,
            174,
            175,
            176,
            177,
            178,
            179,
            180,
            181,
            182,
            183,
            184,
            185,
            186,
            187,
            188,
            189,
            190,
            191,
            192,
            193,
            194,
            195,
            196,
            197,
            198,
            199,
            200,
            201,
            202,
            203,
            204,
            205,
            206,
            207,
            208,
            209,
            210,
            211,
            212,
            213,
            214,
            215,
            216,
            217,
            218,
            219,
            220,
            221,
            222,
            223,
            224,
            225,
            226,
            227,
            228,
            229,
            230,
            231,
            232,
            233,
            234,
            235,
            236,
            237,
            238,
            239,
            240,
            241,
            242,
            243,
            244,
            245,
            246,
            247,
            248,
            249,
            250,
            251,
            252,
            253,
            254,
            255,
            256,
            257,
            258,
            259,
            260,
        ]
        return pd.DataFrame({"Close": prices})

    @staticmethod
    def Ticker(_ticker):
        return _FakeTicker(
            {
                "forwardPE": 17.5,
                "returnOnEquity": 0.24,
                "revenueGrowth": 0.15,
                "operatingMargins": 0.18,
            }
        )


class _FakeSentiment:
    def __init__(self, polarity):
        self.polarity = polarity


class _FakeTextBlob:
    def __init__(self, text):
        polarity = (
            0.5
            if "strong" in text.lower() or "upgrade" in text.lower()
            else -0.2
        )
        self.sentiment = _FakeSentiment(polarity)


def test_hydra_analysis_and_dry_run(monkeypatch):
    monkeypatch.setattr(hydra_bot, "yf", _FakeYFinance)
    monkeypatch.setattr(hydra_bot, "TextBlob", _FakeTextBlob)

    bot = HydraBot(
        HydraConfig(
            alpaca_api_key=None,
            alpaca_secret_key=None,
            alpaca_base_url="https://paper-api.alpaca.markets",
            ibkr_host="127.0.0.1",
            ibkr_port=7497,
            ibkr_client_id=6,
            fastapi_base_url="http://127.0.0.1:8000",
            airbyte_api_base="http://localhost:8001/api/v1",
            airflow_dag_id="hydra_mansa_health",
            mlflow_tracking_uri="http://localhost:5000",
            mlflow_experiment="Hydra_Mansa_Health",
            enable_trading=False,
            enable_mlflow_logging=False,
            momentum_lookback=20,
            technical_short_window=50,
            technical_long_window=200,
            buy_threshold=0.15,
            default_history_period="1y",
            default_history_interval="1d",
            default_universe=("XLV", "UNH"),
        )
    )

    analysis = bot.analyze_ticker(
        "UNH",
        headlines=["Strong healthcare growth drives analyst upgrade"],
    )

    assert analysis["ticker"] == "UNH"
    assert analysis["action"] in {"BUY", "HOLD", "SELL"}
    assert analysis["momentum"]["score"] > 0
    assert analysis["technical"]["signal"] is True

    trade_action = (
        analysis["action"] if analysis["action"] != "HOLD" else "BUY"
    )
    order = bot.execute_trade(
        "alpaca",
        "UNH",
        trade_action,
        qty=5,
    )
    assert order["status"] == "simulated"
    assert order["dry_run"] is True


def test_hydra_fastapi_routes(monkeypatch):
    monkeypatch.setattr(hydra_bot, "yf", _FakeYFinance)
    monkeypatch.setattr(hydra_bot, "TextBlob", _FakeTextBlob)

    bot = HydraBot(
        HydraConfig(
            alpaca_api_key=None,
            alpaca_secret_key=None,
            alpaca_base_url="https://paper-api.alpaca.markets",
            ibkr_host="127.0.0.1",
            ibkr_port=7497,
            ibkr_client_id=6,
            fastapi_base_url="http://127.0.0.1:8000",
            airbyte_api_base="http://localhost:8001/api/v1",
            airflow_dag_id="hydra_mansa_health",
            mlflow_tracking_uri="http://localhost:5000",
            mlflow_experiment="Hydra_Mansa_Health",
            enable_trading=False,
            enable_mlflow_logging=False,
            momentum_lookback=20,
            technical_short_window=50,
            technical_long_window=200,
            buy_threshold=0.15,
            default_history_period="1y",
            default_history_interval="1d",
            default_universe=("XLV", "UNH"),
        )
    )

    monkeypatch.setattr(Main, "get_hydra_bot", lambda: bot)
    monkeypatch.setattr(Main, "HydraBot", HydraBot)

    client = TestClient(Main.app)

    status_response = client.get("/hydra/status")
    assert status_response.status_code == 200
    assert status_response.json()["name"] == "Hydra"

    analyze_response = client.post(
        "/hydra/analyze",
        json={
            "ticker": "UNH",
            "news_headlines": [
                "Strong healthcare growth drives analyst upgrade"
            ],
        },
    )
    assert analyze_response.status_code == 200
    assert "composite_score" in analyze_response.json()
