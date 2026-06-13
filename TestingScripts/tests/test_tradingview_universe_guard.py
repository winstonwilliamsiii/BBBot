from types import SimpleNamespace
import json

from api import index as api_index


def _write_bot_profile(tmp_path, symbols):
    profile_dir = tmp_path / "bots"
    profile_dir.mkdir()

    csv_file = tmp_path / "vega_universe.csv"
    csv_lines = ["Ticker,volume"]
    csv_lines.extend(f"{symbol},1000000" for symbol in symbols)
    csv_file.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")

    (profile_dir / "vega.yml").write_text(
        f"""
bot:
    name: Vega
    runtime_name: Vega_Bot
    fund: Mansa Retail
    strategy: Breakout Strategy
strategy:
    screener_file: {csv_file.name}
    universe: Retail_Breakouts
    position_size: 1000
""".strip(),
        encoding="utf-8",
    )

    return profile_dir


def test_handler_accepts_symbol_in_configured_universe(monkeypatch, tmp_path):
    profile_dir = _write_bot_profile(tmp_path, ["AAPL", "MSFT"])
    monkeypatch.setenv("BOT_CONFIG_PATH", str(profile_dir))
    api_index.BOT_UNIVERSE_CACHE.clear()

    request = SimpleNamespace(
        path="/api/tradingview-alert",
        method="POST",
        json={
            "bot": "Vega_Bot",
            "ticker": "NASDAQ:AAPL",
            "action": "BUY",
        },
    )
    response = api_index.handler(request)
    body = json.loads(response["body"])

    assert response["statusCode"] == 200
    assert body["normalized"]["symbol"] == "AAPL"
    assert body["validation"]["universe"] == "Retail_Breakouts"


def test_handler_rejects_symbol_outside_universe(
    monkeypatch,
    tmp_path,
):
    profile_dir = _write_bot_profile(tmp_path, ["AAPL"])
    monkeypatch.setenv("BOT_CONFIG_PATH", str(profile_dir))
    api_index.BOT_UNIVERSE_CACHE.clear()

    request = SimpleNamespace(
        path="/api/tradingview-alert",
        method="POST",
        json={
            "bot": "Vega_Bot",
            "ticker": "NASDAQ:NFLX",
            "action": "BUY",
        },
    )
    response = api_index.handler(request)
    body = json.loads(response["body"])

    assert response["statusCode"] == 422
    assert body["validation"]["reason"] == "symbol not in configured universe"


def test_handler_rejects_symbol_when_configured_universe_is_empty(
    monkeypatch,
    tmp_path,
):
    profile_dir = _write_bot_profile(tmp_path, [])
    monkeypatch.setenv("BOT_CONFIG_PATH", str(profile_dir))
    api_index.BOT_UNIVERSE_CACHE.clear()

    request = SimpleNamespace(
        path="/api/tradingview-alert",
        method="POST",
        json={
            "bot": "Vega_Bot",
            "ticker": "NASDAQ:AAPL",
            "action": "BUY",
        },
    )

    response = api_index.handler(request)

    assert response["statusCode"] == 422
    assert "Symbol rejected by bot universe guard" in response["body"]
