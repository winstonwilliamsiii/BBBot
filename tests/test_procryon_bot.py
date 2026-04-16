from fastapi.testclient import TestClient

from procryon_bot import ProcryonBot, ProcryonConfig
import Main


def test_procryon_config_from_env_prefers_control_center_and_remote_mt5(
    monkeypatch,
):
    monkeypatch.setenv("CONTROL_CENTER_API_URL", "http://127.0.0.1:5001")
    monkeypatch.setenv("MT5_API_URL", "http://localhost:8002")
    monkeypatch.setenv(
        "AXI_MT5_API_URL",
        "https://example-mt5-bridge.invalid",
    )
    # Ensure real .env FTMO value doesn't override the fallback assertion
    monkeypatch.delenv("FTMO_MT5_API_URL", raising=False)

    config = ProcryonConfig.from_env()
    ftmo_credentials = ProcryonBot(config)._resolve_mt5_credentials("ftmo")

    assert config.fastapi_base_url == "http://127.0.0.1:5001"
    assert ftmo_credentials["api_url"] == "https://example-mt5-bridge.invalid"


def test_procryon_bootstrap_and_evaluate():
    bot = ProcryonBot(ProcryonConfig())
    metrics = bot.bootstrap_demo_models()

    assert metrics["knn_samples"] >= 2
    assert metrics["fnn_samples"] >= 4

    result = bot.evaluate_opportunity(
        [0.0032, 0.0027, 0.0039],
        [32, 0.82, 7, 2, 0.76],
    )

    assert result["platform"] == "MT5"
    assert 0.0 <= result["execution_probability"] <= 1.0
    assert isinstance(result["execute"], bool)


def test_procryon_configure_updates_threshold():
    bot = ProcryonBot(ProcryonConfig())
    response = bot.configure({"execution_threshold": 0.61})

    assert response["updated"]["execution_threshold"] == 0.61
    assert response["config"]["execution_threshold"] == 0.61


def test_procryon_fastapi_routes(monkeypatch):
    bot = ProcryonBot(ProcryonConfig())
    bot.bootstrap_demo_models()

    monkeypatch.setattr(
        Main,
        "get_procryon_bot",
        lambda: bot,
    )
    monkeypatch.setattr(Main, "ProcryonBot", ProcryonBot)

    client = TestClient(Main.app)

    status_response = client.get("/procryon/status")
    assert status_response.status_code == 200
    assert status_response.json()["name"] == "Procryon"

    evaluate_response = client.post(
        "/procryon/evaluate",
        json={
            "spread_vector": [0.0030, 0.0025, 0.0038],
            "execution_features": [30, 0.80, 6, 2, 0.79],
        },
    )
    assert evaluate_response.status_code == 200
    assert "execution_probability" in evaluate_response.json()
