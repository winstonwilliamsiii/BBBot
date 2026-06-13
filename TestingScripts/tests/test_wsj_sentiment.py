from datetime import datetime, timezone

from scripts.sentiment_utils import WsjSentimentService, notify_discord


def test_analyze_headline_maps_positive_response(monkeypatch):
    service = WsjSentimentService(neutral_band=0.15)
    monkeypatch.setattr(
        service,
        "_get_classifier",
        lambda: (lambda _text: [{"label": "POSITIVE", "score": 0.91}]),
    )

    result = service.analyze_headline("Nvidia jumps after earnings")

    assert result["sentiment_label"] == "bullish"
    assert result["sentiment_score"] == 0.91


def test_analyze_headline_maps_negative_response(monkeypatch):
    service = WsjSentimentService(neutral_band=0.15)
    monkeypatch.setattr(
        service,
        "_get_classifier",
        lambda: (lambda _text: [{"label": "NEGATIVE", "score": 0.84}]),
    )

    result = service.analyze_headline("Apple faces weak demand concerns")

    assert result["sentiment_label"] == "bearish"
    assert result["sentiment_score"] == -0.84


def test_infer_tickers_from_headline_aliases():
    service = WsjSentimentService()

    tickers = service.infer_tickers(
        "Amazon and Nvidia rally while Microsoft expands Azure"
    )

    assert tickers == ["AMZN", "MSFT", "NVDA"]


def test_message_id_is_stable():
    service = WsjSentimentService()

    first = service.message_id("headline-1", article_id="abc123")
    second = service.message_id("headline-1", article_id="abc123")

    assert first == second
    assert len(first) == 32


def test_store_sentiment_message_returns_zero_without_mysql():
    service = WsjSentimentService()

    inserted = service.store_sentiment_message(
        tickers=["NVDA"],
        headline="Nvidia extends gains",
        analysis={
            "sentiment_score": 0.5,
            "sentiment_label": "bullish",
        },
        published_at=datetime.now(timezone.utc),
    )

    assert inserted >= 0


def test_build_discord_message_renders_source_and_score():
    service = WsjSentimentService()

    message = service.build_discord_message(
        "Nvidia extends gains",
        {
            "sentiment_label": "bullish",
            "sentiment_score": 0.76,
        },
        ["NVDA"],
    )

    assert "WSJ Headline: Nvidia extends gains" in message
    assert "Tickers: NVDA" in message
    assert "bullish (0.76)" in message


def test_notify_discord_posts_payload(monkeypatch):
    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout

    monkeypatch.setattr("scripts.sentiment_utils.requests.post", fake_post)

    sent = notify_discord(
        "hello",
        webhook_url="https://discord.test/webhook",
    )

    assert sent is True
    assert captured["url"] == "https://discord.test/webhook"
    assert captured["json"] == {"content": "hello"}
    assert captured["timeout"] == 8