from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from functools import lru_cache
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator


app = FastAPI(
    title="Mansa AI Fund Router",
    version="0.1.0",
    description=(
        "Modular FastAPI bridge for Alpaca, IBKR, MT5, and prop-firm "
        "execution connectors."
    ),
)

PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_PATHS = {
    "xgboost": PROJECT_ROOT / "models" / "xgboost_model.pkl",
    "randomforest": PROJECT_ROOT / "models" / "randomforest_model.pkl",
}


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class PropFirmName(str, Enum):
    FTMO = "FTMO"
    AXI = "AXI"
    ZENIT = "ZENIT"


class BrokerOrderRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    qty: float = Field(gt=0)
    side: OrderSide
    client_order_id: str | None = Field(default=None, max_length=64)
    account_id: str | None = Field(default=None, max_length=64)
    conid: int | None = Field(default=None, gt=0)
    order_type: str = Field(default="MKT", max_length=16)
    time_in_force: str = Field(default="DAY", max_length=16)
    price: float | None = Field(default=None, gt=0)
    notional: float | None = Field(default=None, gt=0)
    stop_loss: float | None = Field(default=None, gt=0)
    take_profit: float | None = Field(default=None, gt=0)
    exchange: str | None = Field(default=None, max_length=32)
    extended_hours: bool = False
    dry_run: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, value: Any) -> str:
        symbol = str(value or "").strip().upper()
        if not symbol:
            raise ValueError("symbol is required")
        return symbol


class PropFirmOrderRequest(BrokerOrderRequest):
    firm: PropFirmName


class PredictionRequest(BaseModel):
    features: list[float] = Field(min_length=1)


def _clean_env_text(value: Any) -> str:
    cleaned = str(value or "").strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in ("'", '"'):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def _as_int(value: Any, default: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return default


def _as_bool(value: Any, default: bool = False) -> bool:
    cleaned = _clean_env_text(value).lower()
    if not cleaned:
        return default
    return cleaned in {"1", "true", "yes", "y", "on"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _routing_manifest() -> dict[str, list[str]]:
    return {
        "inference": [
            "/ml/xgboost/predict",
            "/ml/randomforest/predict",
        ],
        "execution": [
            "/broker/alpaca/order",
            "/broker/ibkr/order",
            "/broker/mt5/order",
            "/broker/prop/order",
        ],
    }


def _health_payload(name: str, status: str = "online") -> dict[str, Any]:
    return {
        "broker": name,
        "status": status,
        "timestamp": _utc_now(),
    }


def _mock_submit_order(
    broker: str,
    payload: BrokerOrderRequest,
) -> dict[str, Any]:
    return {
        "status": "accepted",
        "broker": broker,
        "symbol": payload.symbol,
        "qty": payload.qty,
        "side": payload.side.value,
        "client_order_id": payload.client_order_id,
        "timestamp": _utc_now(),
    }


def _resolve_mt5_credentials(prefix: str | None = None) -> dict[str, Any]:
    prefix = (prefix or "MT5").upper()
    api_url = (
        _clean_env_text(os.getenv(f"{prefix}_MT5_API_URL"))
        or _clean_env_text(os.getenv("MT5_API_URL"))
        or "http://localhost:8002"
    )
    user = (
        _clean_env_text(os.getenv(f"{prefix}_MT5_USER"))
        or _clean_env_text(os.getenv("MT5_USER"))
        or _clean_env_text(os.getenv("MT5_LOGIN"))
    )
    password = (
        _clean_env_text(os.getenv(f"{prefix}_MT5_PASSWORD"))
        or _clean_env_text(os.getenv("MT5_PASSWORD"))
    )
    host = (
        _clean_env_text(os.getenv(f"{prefix}_MT5_SERVER"))
        or _clean_env_text(os.getenv(f"{prefix}_MT5_HOST"))
        or _clean_env_text(os.getenv("MT5_SERVER"))
        or _clean_env_text(os.getenv("MT5_HOST"))
    )
    port = _as_int(
        _clean_env_text(os.getenv(f"{prefix}_MT5_PORT"))
        or _clean_env_text(os.getenv("MT5_PORT")),
        443,
    )
    missing = [
        name
        for name, value in {
            "user": user,
            "password": password,
            "host": host,
        }.items()
        if not value
    ]
    return {
        "api_url": api_url,
        "user": user,
        "password": password,
        "host": host,
        "port": port,
        "missing": missing,
    }


def _normalized_execution_response(
    *,
    status: str,
    broker: str,
    payload: BrokerOrderRequest,
    raw: Any,
    connector: str,
    **extra: Any,
) -> dict[str, Any]:
    response = {
        "status": status,
        "broker": broker,
        "connector": connector,
        "symbol": payload.symbol,
        "qty": payload.qty,
        "side": payload.side.value,
        "client_order_id": payload.client_order_id,
        "timestamp": _utc_now(),
        "raw": raw,
    }
    response.update(extra)
    return response


def _submit_alpaca_order(payload: BrokerOrderRequest) -> dict[str, Any]:
    if payload.dry_run:
        return _normalized_execution_response(
            status="dry_run",
            broker="Alpaca",
            payload=payload,
            raw=_mock_submit_order("Alpaca", payload),
            connector="AlpacaConnector",
            mode="paper" if _as_bool(os.getenv("ALPACA_PAPER"), True) else "live",
        )

    api_key = _clean_env_text(os.getenv("ALPACA_API_KEY"))
    secret_key = _clean_env_text(os.getenv("ALPACA_SECRET_KEY"))
    if not api_key or not secret_key:
        raise HTTPException(
            status_code=503,
            detail="Missing Alpaca credentials: ALPACA_API_KEY / ALPACA_SECRET_KEY",
        )

    from frontend.components.alpaca_connector import AlpacaConnector

    paper = _as_bool(os.getenv("ALPACA_PAPER"), True)
    connector = AlpacaConnector(api_key=api_key, secret_key=secret_key, paper=paper)
    result = connector.place_order(
        symbol=payload.symbol,
        qty=None if payload.notional is not None else payload.qty,
        notional=payload.notional,
        side=payload.side.value.lower(),
        order_type=payload.order_type.lower(),
        time_in_force=payload.time_in_force.lower(),
        limit_price=payload.price,
        stop_price=payload.stop_loss,
        extended_hours=payload.extended_hours,
    )
    if not result:
        raise HTTPException(
            status_code=502,
            detail=f"Alpaca order failed: {connector.last_error or 'unknown error'}",
        )

    return _normalized_execution_response(
        status="submitted",
        broker="Alpaca",
        payload=payload,
        raw=result,
        connector="AlpacaConnector",
        mode="paper" if paper else "live",
        order_id=result.get("id"),
    )


def _resolve_ibkr_conid(client: Any, payload: BrokerOrderRequest) -> int:
    if payload.conid:
        return payload.conid

    metadata_conid = payload.metadata.get("conid")
    if metadata_conid:
        return _as_int(metadata_conid, 0)

    cleaned_symbol = payload.symbol.replace("/", "").replace(".", "").upper()
    exchange = payload.exchange or str(payload.metadata.get("exchange") or "IDEALPRO")
    if len(cleaned_symbol) == 6:
        resolved = client.resolve_forex_conid(payload.symbol, exchange=exchange)
        if resolved:
            return resolved

    raise HTTPException(
        status_code=400,
        detail=(
            "IBKR orders require `conid` for non-FOREX symbols. Provide `conid` "
            "directly or use a 6-character forex symbol for auto-resolution."
        ),
    )


def _submit_ibkr_order(payload: BrokerOrderRequest) -> dict[str, Any]:
    gateway_url = _clean_env_text(os.getenv("IBKR_GATEWAY_URL")) or "https://localhost:5000"
    account_id = payload.account_id or _clean_env_text(os.getenv("IBKR_ACCOUNT_ID"))
    if not account_id:
        raise HTTPException(
            status_code=503,
            detail="Missing IBKR_ACCOUNT_ID for order routing",
        )

    from frontend.components.ibkr_gateway_client import GatewayConfig, IBKRGatewayClient

    config = GatewayConfig(
        gateway_path=_clean_env_text(os.getenv("IBKR_GATEWAY_PATH")),
        base_url=gateway_url,
        account_id=account_id,
        verify_ssl=_as_bool(os.getenv("IBKR_GATEWAY_VERIFY_SSL"), False),
    )
    client = IBKRGatewayClient(config)

    if payload.dry_run:
        return _normalized_execution_response(
            status="dry_run",
            broker="IBKR",
            payload=payload,
            raw=_mock_submit_order("IBKR", payload),
            connector="IBKRGatewayClient",
            account_id=account_id,
            gateway_url=gateway_url,
        )

    client.start_gateway()
    conid = _resolve_ibkr_conid(client, payload)
    result = client.place_order(
        conid=conid,
        side=payload.side.value,
        quantity=payload.qty,
        account_id=account_id,
        order_type=payload.order_type.upper(),
        tif=payload.time_in_force.upper(),
        price=payload.price,
    )
    if not result:
        raise HTTPException(
            status_code=502,
            detail="IBKR order failed or gateway authentication is unavailable",
        )

    return _normalized_execution_response(
        status="submitted",
        broker="IBKR",
        payload=payload,
        raw=result,
        connector="IBKRGatewayClient",
        account_id=account_id,
        gateway_url=gateway_url,
        conid=conid,
    )


def _mt5_order_type(payload: BrokerOrderRequest) -> str:
    normalized = payload.order_type.upper()
    if normalized in {"MKT", "MARKET"}:
        return payload.side.value
    if normalized == "LIMIT":
        return f"{payload.side.value}_LIMIT"
    if normalized == "STOP":
        return f"{payload.side.value}_STOP"
    return normalized


def _submit_mt5_order(
    payload: BrokerOrderRequest,
    venue: str = "MT5",
) -> dict[str, Any]:
    credentials = _resolve_mt5_credentials(venue)
    if credentials["missing"]:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Missing {venue} MT5 credentials: "
                + ", ".join(credentials["missing"])
            ),
        )

    if payload.dry_run:
        return _normalized_execution_response(
            status="dry_run",
            broker=venue,
            payload=payload,
            raw=_mock_submit_order(venue, payload),
            connector="MT5Connector",
            api_url=credentials["api_url"],
        )

    from frontend.components.mt5_connector import MT5Connector

    connector = MT5Connector(base_url=credentials["api_url"])
    connected = connector.connect(
        user=credentials["user"],
        password=credentials["password"],
        host=credentials["host"],
        port=credentials["port"],
    )
    if not connected:
        raise HTTPException(
            status_code=502,
            detail=(
                f"{venue} MT5 bridge connection failed: "
                f"{connector.last_connect_error or 'unknown error'}"
            ),
        )

    result = connector.place_trade(
        symbol=payload.symbol,
        order_type=_mt5_order_type(payload),
        volume=payload.qty,
        price=payload.price,
        sl=payload.stop_loss,
        tp=payload.take_profit,
        comment=payload.client_order_id or f"{venue}-router",
    )
    if not result:
        raise HTTPException(
            status_code=502,
            detail=f"{venue} MT5 order failed",
        )

    return _normalized_execution_response(
        status="submitted",
        broker=venue,
        payload=payload,
        raw=result,
        connector="MT5Connector",
        api_url=credentials["api_url"],
    )


@lru_cache(maxsize=4)
def _load_model(model_name: str):
    model_path = MODEL_PATHS.get(model_name)
    if model_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown model: {model_name}",
        )
    if not model_path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Model artifact is unavailable: {model_path.name}",
        )

    try:
        import joblib
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="joblib is required for ML inference endpoints",
        ) from exc

    try:
        return joblib.load(model_path)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load {model_name} model",
        ) from exc


def _predict(model_name: str, payload: PredictionRequest) -> dict[str, Any]:
    try:
        import numpy as np
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="numpy is required for ML inference endpoints",
        ) from exc

    model = _load_model(model_name)
    try:
        features = np.array(payload.features, dtype=float).reshape(1, -1)
        prediction = model.predict(features)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed for {model_name}",
        ) from exc

    return {
        "model": model_name,
        "prediction": (
            prediction.tolist()
            if hasattr(prediction, "tolist")
            else prediction
        ),
        "timestamp": _utc_now(),
    }
# --- Gradio Demo Endpoint ---
@app.get("/ui/gradio/altair")
def gradio_altair():
    def predict_fn(rsi, sentiment, macro):
        features = [rsi, sentiment, macro]
        prediction = xgb_model.predict(np.array(features).reshape(1, -1))
        return f"Predicted Trade Signal: {prediction[0]}"

    demo = gr.Interface(
        fn=predict_fn,
        inputs=["number", "number", "number"],
        outputs="text",
        title="Altair (Mansa AI) News Trading Demo"
    )
    demo.launch(share=True)
    return {"status": "Gradio Altair demo launched"}
# --- Optuna Tuning Endpoint ---
@app.post("/ml/optuna/tune")
def optuna_tune(n_trials: int = 50):
    def objective(trial):
        max_depth = trial.suggest_int("max_depth", 3, 10)
        learning_rate = trial.suggest_float("learning_rate", 0.01, 0.3)
        subsample = trial.suggest_float("subsample", 0.5, 1.0)
        # Example: use XGBoost trial here
        # Replace with actual training/validation loop
        score = (max_depth * learning_rate * subsample)  # dummy score
        return score

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)
    return {"best_params": study.best_params, "best_value": study.best_value}
def health() -> dict[str, Any]:
@app.get("/health")
    return {
        "status": "operational",
        "timestamp": _utc_now(),
        "brokers": {
            "alpaca": _health_payload("Alpaca"),
            "ibkr": _health_payload("IBKR"),
            "mt5": _health_payload("MT5"),
            "prop": _health_payload("PropConnectors"),
        },
        "ml_models": {
            name: "available" if path.exists() else "missing"
            for name, path in MODEL_PATHS.items()
        },
        "routing": _routing_manifest(),
    }


@app.get("/broker/alpaca/health")
def alpaca_health() -> dict[str, Any]:
    return _health_payload("Alpaca")


@app.post("/broker/alpaca/order")
def alpaca_order(payload: BrokerOrderRequest) -> dict[str, Any]:
    return _submit_alpaca_order(payload)


@app.get("/broker/ibkr/health")
def ibkr_health() -> dict[str, Any]:
    return _health_payload("IBKR")


@app.post("/broker/ibkr/order")
def ibkr_order(payload: BrokerOrderRequest) -> dict[str, Any]:
    return _submit_ibkr_order(payload)


@app.get("/broker/mt5/health")
def mt5_health() -> dict[str, Any]:
    return _health_payload("MT5")


@app.post("/broker/mt5/order")
def mt5_order(payload: BrokerOrderRequest) -> dict[str, Any]:
    return _submit_mt5_order(payload)


@app.get("/broker/prop/health")
def prop_health() -> dict[str, Any]:
    return {
        "broker": "PropConnectors",
        "status": "online",
        "timestamp": _utc_now(),
        "firms": {
            firm.value.lower(): _resolve_mt5_credentials(firm.value)
            for firm in PropFirmName
        },
    }


@app.post("/broker/prop/order")
def prop_order(payload: PropFirmOrderRequest) -> dict[str, Any]:
    result = _submit_mt5_order(payload, venue=payload.firm.value)
    result["firm"] = payload.firm.value
    return result


@app.post("/ml/xgboost/predict")
def xgboost_predict(payload: PredictionRequest) -> dict[str, Any]:
    return _predict("xgboost", payload)


@app.post("/ml/randomforest/predict")
def randomforest_predict(payload: PredictionRequest) -> dict[str, Any]:
    return _predict("randomforest", payload)
