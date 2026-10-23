from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api import notifier


def _client():
    app = FastAPI()
    app.include_router(notifier.router)
    return TestClient(app)


def test_signal_payload_routes_with_cosmic_score_and_ml_insights(monkeypatch):
    sent = []
    monkeypatch.setenv("WEBHOOK_TITAN", "https://discord.example/titan")
    monkeypatch.setattr(notifier, "send_to_discord", lambda url, payload: sent.append((url, payload)))

    response = _client().post(
        "/notify/signal",
        json={
            "bot_name": "Titan",
            "symbol": "EURUSD",
            "decision": "BUY",
            "cosmic_score": 72.5,
            "mode": "live",
            "heads": {"trend": "bullish"},
        },
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert sent[0][0] == "https://discord.example/titan"
    embed = sent[0][1]["embeds"][0]
    assert embed["title"] == "EURUSD — BUY"
    assert "Cosmic Score: 72.5" in embed["description"]
    assert '"trend": "bullish"' in embed["description"]
    assert sent[0][1]["allowed_mentions"] == {"parse": []}


def test_tradingview_alert_requires_and_does_not_forward_secret(monkeypatch):
    sent = []
    monkeypatch.setenv("TRADINGVIEW_WEBHOOK_SECRET", "shared-secret")
    monkeypatch.setenv("WEBHOOK_VEGA", "https://discord.example/vega")
    monkeypatch.setattr(notifier, "send_to_discord", lambda url, payload: sent.append((url, payload)))

    client = _client()
    invalid = client.post(
        "/tv-alert",
        json={"bot_name": "Vega", "secret": "wrong-secret"},
    )
    valid = client.post(
        "/tv-alert",
        json={
            "bot_name": "Vega",
            "secret": "shared-secret",
            "screenshot": "https://charts.example/chart.png",
            "message": "EURUSD setup",
        },
    )

    assert invalid.status_code == 401
    assert valid.status_code == 200
    assert sent[0][0] == "https://discord.example/vega"
    assert sent[0][1]["content"] == "**Vega Chart Update**\nEURUSD setup"
    assert sent[0][1]["embeds"] == [
        {"image": {"url": "https://charts.example/chart.png"}}
    ]
    assert "secret" not in str(sent[0][1])


def test_tradingview_fails_closed_when_secret_is_not_configured(monkeypatch):
    monkeypatch.delenv("TRADINGVIEW_WEBHOOK_SECRET", raising=False)

    response = _client().post(
        "/tv-alert",
        json={"bot_name": "Vega", "secret": "any-value"},
    )

    assert response.status_code == 503


def test_missing_bot_webhook_returns_service_unavailable(monkeypatch):
    monkeypatch.delenv("WEBHOOK_TITAN", raising=False)

    response = _client().post(
        "/notify/signal",
        json={
            "bot_name": "Titan",
            "symbol": "EURUSD",
            "decision": "BUY",
        },
    )

    assert response.status_code == 503


def test_discord_delivery_error_is_returned_to_caller(monkeypatch):
    monkeypatch.setenv("WEBHOOK_TITAN", "https://discord.example/titan")

    def fail_delivery(url, payload):
        raise notifier.requests.ConnectionError("connection failed")

    monkeypatch.setattr(notifier, "send_to_discord", fail_delivery)

    response = _client().post(
        "/notify/signal",
        json={
            "bot_name": "Titan",
            "symbol": "EURUSD",
            "decision": "BUY",
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Discord webhook delivery failed"
