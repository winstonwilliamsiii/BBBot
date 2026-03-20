import importlib

import streamlit as st


def test_alpaca_config_reads_uppercase_keys_from_alpaca_section(monkeypatch):
    monkeypatch.delenv("ALPACA_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_SECRET_KEY", raising=False)
    monkeypatch.delenv("ALPACA_PAPER", raising=False)

    monkeypatch.setattr(
        st,
        "secrets",
        {
            "alpaca": {
                "ALPACA_API_KEY": "PKSECTIONKEY",
                "ALPACA_SECRET_KEY": "section-secret",
                "ALPACA_PAPER": "true",
            }
        },
        raising=False,
    )

    module = importlib.import_module("frontend.utils.secrets_helper")
    config = module.get_alpaca_config()

    assert config["api_key"] == "PKSECTIONKEY"
    assert config["secret_key"] == "section-secret"
    assert config["paper"] is True


def test_alpaca_config_prefers_explicit_paper_pair_in_alpaca_section(monkeypatch):
    monkeypatch.delenv("ALPACA_PAPER_API_KEY", raising=False)
    monkeypatch.delenv("ALPACA_PAPER_SECRET_KEY", raising=False)
    monkeypatch.delenv("ALPACA_PAPER", raising=False)

    monkeypatch.setattr(
        st,
        "secrets",
        {
            "alpaca": {
                "ALPACA_PAPER_API_KEY": "PKPAPERKEY",
                "ALPACA_PAPER_SECRET_KEY": "paper-secret",
                "ALPACA_LIVE_API_KEY": "AKLIVEKEY",
                "ALPACA_LIVE_SECRET_KEY": "live-secret",
                "ALPACA_PAPER": "true",
            }
        },
        raising=False,
    )

    module = importlib.import_module("frontend.utils.secrets_helper")
    config = module.get_alpaca_config()

    assert config["api_key"] == "PKPAPERKEY"
    assert config["secret_key"] == "paper-secret"
    assert config["paper"] is True