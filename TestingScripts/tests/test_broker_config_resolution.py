from frontend.utils import secrets_helper


def test_alpaca_config_reads_uppercase_keys_from_alpaca_section(monkeypatch):
    values = {
        ("ALPACA_API_KEY", "alpaca"): "PKSECTIONKEY",
        ("ALPACA_SECRET_KEY", "alpaca"): "section-secret",
        ("ALPACA_PAPER", "alpaca"): "true",
    }

    monkeypatch.setattr(
        secrets_helper,
        "get_secret",
        lambda key, default=None, section=None: values.get((key, section), default),
    )
    monkeypatch.delenv("ALPACA_PAPER", raising=False)

    config = secrets_helper.get_alpaca_config()

    assert config["api_key"] == "PKSECTIONKEY"
    assert config["secret_key"] == "section-secret"
    assert config["paper"] is True


def test_alpaca_config_prefers_explicit_paper_pair_in_alpaca_section(monkeypatch):
    values = {
        ("ALPACA_PAPER_API_KEY", "alpaca"): "PKPAPERKEY",
        ("ALPACA_PAPER_SECRET_KEY", "alpaca"): "paper-secret",
        ("ALPACA_LIVE_API_KEY", "alpaca"): "AKLIVEKEY",
        ("ALPACA_LIVE_SECRET_KEY", "alpaca"): "live-secret",
        ("ALPACA_PAPER", "alpaca"): "true",
    }

    monkeypatch.setattr(
        secrets_helper,
        "get_secret",
        lambda key, default=None, section=None: values.get((key, section), default),
    )
    monkeypatch.delenv("ALPACA_PAPER", raising=False)

    config = secrets_helper.get_alpaca_config()

    assert config["api_key"] == "PKPAPERKEY"
    assert config["secret_key"] == "paper-secret"
    assert config["paper"] is True