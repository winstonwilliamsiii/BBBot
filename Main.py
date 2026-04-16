from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal, Optional, Any

import json

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
import requests

from backend.api.admin.liquidity_manager import LiquidityManager
from backend.api.hydra_persistence import (
    persist_hydra_analysis,
    persist_hydra_trade_decision,
)

try:
    import pymysql
except ImportError:
    pymysql = None

try:
    from procryon_bot import ProcryonBot

    PROCRYON_IMPORT_ERROR = None
except (ImportError, OSError, RuntimeError, ValueError) as exc:
    ProcryonBot = None
    PROCRYON_IMPORT_ERROR = str(exc)

try:
    from hydra_bot import HydraBot

    HYDRA_IMPORT_ERROR = None
except (ImportError, OSError, RuntimeError, ValueError) as exc:
    HydraBot = None
    HYDRA_IMPORT_ERROR = str(exc)

try:
    from triton_bot import TritonBot

    TRITON_IMPORT_ERROR = None
except (ImportError, OSError, RuntimeError, ValueError) as exc:
    TritonBot = None
    TRITON_IMPORT_ERROR = str(exc)

from draco_bot import app as draco_app
from vega_bot import app as vega_app
from frontend.components.ibkr_gateway_client import (
    GatewayConfig,
    IBKRGatewayClient,
)
from frontend.utils.discord_alpaca import send_discord_trade_notification as _discord_trade
from scripts.webhook_ws import router as sentiment_router

app = FastAPI(
    title="Bentley Budget Bot API",
    version="0.2.0",
    description=(
        "Unified FastAPI service for Bentley Budget Bot, including the "
        "control center, bot APIs, and platform health probes."
    ),
)

API_VERSION = "0.2.0"

_BROKER_MODES_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__) or "."), "config", "broker_modes.json"
)


def _is_bot_active(bot_name: str) -> bool:
    """Return True if *bot_name* is marked active in config/broker_modes.json."""
    try:
        with open(_BROKER_MODES_PATH, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
        return bool(data.get("active_bots", {}).get(bot_name, False))
    except (OSError, json.JSONDecodeError, KeyError):
        return False


def _notify_bot_trade(bot_name: str, trade_result: dict[str, Any]) -> None:
    """Send a Discord Bot_Talk notification for a submitted or simulated bot trade.

    Never raises — Discord failure must not break the trade response.
    """
    status = trade_result.get("status", "")
    if status not in ("submitted", "simulated", "dry_run"):
        return
    try:
        side = trade_result.get("action") or trade_result.get("side") or ""
        order_id = trade_result.get("order_id")
        id_suffix = f" | order_id: {order_id}" if order_id else ""
        _discord_trade(
            symbol=str(trade_result.get("ticker", "")),
            side=str(side),
            qty=float(trade_result.get("qty", 0)),
            order_type="market",
            status=f"[{bot_name}] {status}{id_suffix}",
        )
    except Exception:
        pass


class IBKROrderRequest(BaseModel):
    conid: int
    side: Literal["BUY", "SELL"]
    quantity: float = Field(gt=0)
    account_id: Optional[str] = None
    order_type: str = "MKT"
    tif: str = "DAY"
    price: Optional[float] = None


class IBKRForexOrderRequest(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: float = Field(gt=0)
    account_id: Optional[str] = None
    exchange: str = "IDEALPRO"
    order_type: str = "MKT"
    tif: str = "DAY"


class IBKRResolveForexRequest(BaseModel):
    symbol: str
    exchange: str = "IDEALPRO"


class ProcryonEvaluateRequest(BaseModel):
    spread_vector: list[float] = Field(min_length=3, max_length=3)
    execution_features: list[float] = Field(min_length=5, max_length=5)


class ProcryonConfigureRequest(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)


class HydraAnalyzeRequest(BaseModel):
    ticker: str = Field(min_length=1)
    news_headlines: list[str] = Field(default_factory=list)


class HydraConfigureRequest(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)


class TritonAnalyzeRequest(BaseModel):
    ticker: str = Field(min_length=1)
    news_headlines: list[str] = Field(default_factory=list)


class TritonTradeRequest(BaseModel):
    broker: Literal["alpaca", "ibkr"]
    ticker: str = Field(min_length=1)
    action: Literal["BUY", "SELL"]
    qty: float = Field(gt=0)
    dry_run: bool = True


class TritonConfigureRequest(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)


class LiquiditySettingsRequest(BaseModel):
    liquidity_buffer_pct: Optional[float] = Field(default=None, ge=0, le=100)
    profit_benchmark_pct: Optional[float] = Field(default=None, ge=0)
    auto_rebalance: Optional[bool] = None


class ProfitBenchmarkRequest(BaseModel):
    position_profit_pct: float


def _is_truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _float_env(name: str, default: float) -> float:
    try:
        return float(str(os.getenv(name, default)).strip())
    except (TypeError, ValueError):
        return default


def _int_env(name: str, default: int) -> int:
    try:
        return int(str(os.getenv(name, default)).strip())
    except (TypeError, ValueError):
        return default


def _service_status(status: str, detail: str, **extra: Any) -> dict[str, Any]:
    payload = {"status": status, "detail": detail}
    payload.update(extra)
    return payload


def _http_probe(
    urls: list[str],
    *,
    timeout: float = 2.0,
    expected_statuses: tuple[int, ...] = (200,),
) -> dict[str, Any]:
    errors: list[str] = []

    for url in urls:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code in expected_statuses:
                return _service_status(
                    "healthy",
                    f"HTTP {response.status_code}",
                    url=url,
                    status_code=response.status_code,
                )

            errors.append(f"{url} -> HTTP {response.status_code}")
        except requests.RequestException as exc:
            errors.append(f"{url} -> {exc}")

    detail = errors[-1] if errors else "No probe URLs configured"
    return _service_status("unhealthy", detail, probes=urls)


def _mysql_provider(host: str) -> str:
    normalized_host = host.strip().lower()
    if "rlwy" in normalized_host or "railway" in normalized_host:
        return "railway"
    return "local"


def _mysql_health() -> dict[str, Any]:
    host = os.getenv("MYSQL_HOST", "127.0.0.1").strip()
    port = _int_env("MYSQL_PORT", 3307)
    user = os.getenv("MYSQL_USER", "root")
    database = os.getenv("MYSQL_DATABASE", "mansa_bot")
    provider = _mysql_provider(host)

    if pymysql is None:
        return _service_status(
            "unavailable",
            "pymysql is not installed in this environment",
            host=host,
            port=port,
            database=database,
            provider=provider,
        )

    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=os.getenv("MYSQL_PASSWORD", "root"),
            database=database,
            connect_timeout=2,
            read_timeout=2,
            write_timeout=2,
        )
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
        connection.close()
        return _service_status(
            "healthy",
            "MySQL connection succeeded",
            host=host,
            port=port,
            database=database,
            provider=provider,
            version=version[0] if version else None,
        )
    except pymysql.MySQLError as exc:
        return _service_status(
            "unhealthy",
            str(exc),
            host=host,
            port=port,
            database=database,
            provider=provider,
        )


def _mlflow_health() -> dict[str, Any]:
    tracking_uri = os.getenv(
        "MLFLOW_TRACKING_URI",
        "http://localhost:5000",
    ).strip()
    return _http_probe(
        [
            f"{tracking_uri.rstrip('/')}/health",
            f"{tracking_uri.rstrip('/')}/version",
            tracking_uri,
        ]
    ) | {"tracking_uri": tracking_uri}


def _appwrite_health() -> dict[str, Any]:
    endpoint = os.getenv("APPWRITE_ENDPOINT", "").strip()
    project_id = os.getenv("APPWRITE_PROJECT_ID", "").strip()
    if not endpoint:
        return _service_status(
            "not_configured",
            "APPWRITE_ENDPOINT is not configured",
            project_id=project_id or None,
        )

    return _http_probe(
        [
            f"{endpoint.rstrip('/')}/health/version",
            f"{endpoint.rstrip('/')}/health",
        ]
    ) | {
        "endpoint": endpoint,
        "project_id": project_id or None,
    }


def _bentley_ui_health() -> dict[str, Any]:
    base_url = os.getenv(
        "BENTLEY_UI_URL",
        os.getenv("STREAMLIT_PUBLIC_URL", "http://localhost:8501"),
    ).strip()
    return _http_probe([f"{base_url.rstrip('/')}/_stcore/health"]) | {
        "base_url": base_url,
    }


def _build_platform_health() -> dict[str, Any]:
    services = {
        "fastapi": _service_status(
            "healthy",
            "FastAPI application is running",
            docs_url="/docs",
            openapi_url="/openapi.json",
        ),
        "mysql": _mysql_health(),
        "mlflow": _mlflow_health(),
        "appwrite": _appwrite_health(),
        "bentley_ui": _bentley_ui_health(),
    }

    statuses = [service["status"] for service in services.values()]
    if any(status == "unhealthy" for status in statuses):
        summary = "degraded"
    elif any(status == "unavailable" for status in statuses):
        summary = "partial"
    else:
        summary = "healthy"

    return {
        "status": summary,
        "services": services,
    }


@lru_cache(maxsize=1)
def get_ibkr_client() -> IBKRGatewayClient:
    config = GatewayConfig(
        gateway_path=os.getenv("IBKR_GATEWAY_PATH", ""),
        base_url=os.getenv("IBKR_GATEWAY_URL", "https://localhost:5000"),
        username=os.getenv("IBKR_USERNAME"),
        password=os.getenv("IBKR_PASSWORD"),
        account_id=os.getenv("IBKR_ACCOUNT_ID", "U14774118"),
    )
    return IBKRGatewayClient(config)


@lru_cache(maxsize=1)
def get_procryon_bot() -> Any:
    if ProcryonBot is None:
        raise RuntimeError(PROCRYON_IMPORT_ERROR or "Procryon unavailable")
    bot = ProcryonBot()
    bot.bootstrap_demo_models()
    return bot


@lru_cache(maxsize=1)
def get_hydra_bot() -> Any:
    if HydraBot is None:
        raise RuntimeError(HYDRA_IMPORT_ERROR or "Hydra unavailable")
    bot = HydraBot()
    bot.bootstrap_demo_state()
    return bot


@lru_cache(maxsize=1)
def get_triton_bot() -> Any:
    if TritonBot is None:
        raise RuntimeError(TRITON_IMPORT_ERROR or "Triton unavailable")
    bot = TritonBot()
    bot.bootstrap_demo_state()
    return bot


@lru_cache(maxsize=1)
def get_liquidity_manager() -> LiquidityManager:
    return LiquidityManager(
        liquidity_buffer_pct=_float_env("LIQUIDITY_BUFFER_PCT", 25.0),
        profit_benchmark_pct=_float_env("PROFIT_BENCHMARK_PCT", 15.0),
        auto_rebalance=_is_truthy(os.getenv("AUTO_REBALANCE", "true")),
    )


def _probe_ibkr_auth_endpoint(url: str, timeout: int = 3) -> dict:
    endpoint = f"{url.rstrip('/')}/v1/api/iserver/auth/status"
    result = {
        "url": url,
        "endpoint": endpoint,
        "ok": False,
        "authenticated": None,
        "status_code": None,
        "error": None,
        "sample": None,
    }

    try:
        resp = requests.get(endpoint, timeout=timeout, verify=False)
        result["status_code"] = resp.status_code
        sample = (resp.text or "")[:180]
        result["sample"] = sample

        if resp.status_code != 200:
            return result

        try:
            body = resp.json()
        except ValueError:
            result["error"] = "non_json_response"
            return result

        if isinstance(body, dict) and "authenticated" in body:
            result["ok"] = True
            result["authenticated"] = bool(body.get("authenticated", False))
            result["sample"] = str({
                "authenticated": body.get("authenticated"),
                "connected": body.get("connected"),
            })
        else:
            result["error"] = "missing_authenticated_field"

        return result

    except requests.RequestException as exc:
        result["error"] = str(exc)
        return result


@app.get("/")
async def root():
    return {
        "message": "Bentley Budget Bot API",
        "service": "fastapi",
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/health",
        "platform_health": "/platform/health",
        "platform_architecture": "/platform/architecture",
    }


@app.get("/version")
async def version():
    return {
        "service": "Bentley Budget Bot API",
        "version": API_VERSION,
    }


@app.get("/health")
@app.get("/api/health")
async def health():
    platform = _build_platform_health()
    return {
        "status": "healthy",
        "service": "Bentley Budget Bot API",
        "version": API_VERSION,
        "platform_status": platform["status"],
        "services": platform["services"],
    }


@app.get("/healthz")
async def healthz():
    return await health()



@app.get("/status")
@app.get("/api/status")
async def status():
    platform = _build_platform_health()
    return {
        "status": platform["status"],
        "service": "Bentley Budget Bot API",
        "version": API_VERSION,
        "services": platform["services"],
    }


@app.get("/status/migration")
async def migration_status():
    return {
        "status": "not_configured",
        "detail": (
            "Database migration status is not exposed by the FastAPI service. "
            "Use the migration workflows or scripts for schema operations."
        ),
    }


@app.get("/platform/architecture")
async def platform_architecture():
    mysql_host = os.getenv("MYSQL_HOST", "127.0.0.1").strip()
    mysql_port = _int_env("MYSQL_PORT", 3307)
    mysql_database = os.getenv("MYSQL_DATABASE", "mansa_bot")
    mlflow_tracking_uri = os.getenv(
        "MLFLOW_TRACKING_URI",
        "http://localhost:5000",
    )
    bentley_ui_url = os.getenv(
        "BENTLEY_UI_URL",
        os.getenv("STREAMLIT_PUBLIC_URL", "http://localhost:8501"),
    ).strip()
    appwrite_endpoint = os.getenv("APPWRITE_ENDPOINT", "").strip()

    return {
        "frontend": {
            "bentley_ui": bentley_ui_url,
            "streamlit_entrypoint": "streamlit_app.py",
            "admin_page": "pages/99_🔧_Admin_Control_Center.py",
        },
        "backend": {
            "fastapi_entrypoint": "Main.py",
            "control_center_default_url": "http://localhost:5001",
            "vercel_handler": "api/index.py",
        },
        "data": {
            "mysql": {
                "host": mysql_host,
                "port": mysql_port,
                "database": mysql_database,
                "provider": _mysql_provider(mysql_host),
            },
            "mlflow_tracking_uri": mlflow_tracking_uri,
            "appwrite_endpoint": appwrite_endpoint or None,
        },
        "docker": {
            "app": "docker/docker-compose.yml",
            "consolidated": "docker/docker-compose-consolidated.yml",
            "mlflow": "docker/docker-compose-mlflow.yml",
            "airflow": "docker/docker-compose-airflow.yml",
        },
    }


@app.get("/platform/health")
@app.get("/api/admin/platform/health")
async def platform_health():
    return _build_platform_health()


@app.get("/admin/liquidity")
@app.get("/api/admin/liquidity")
async def liquidity_metrics(
    total_value: float = Query(default=100000, gt=0),
    current_cash: float = Query(default=26500, ge=0),
    positions_value: float = Query(default=73500, ge=0),
):
    manager = get_liquidity_manager()
    metrics = manager.calculate_liquidity_metrics(
        total_value,
        current_cash,
        positions_value,
    )
    recommendation = manager.get_rebalance_recommendation(metrics)
    max_position = manager.calculate_max_position_size(metrics)
    return {
        "status": "success",
        "metrics": metrics,
        "recommendation": recommendation,
        "max_position_size": max_position,
        "settings": {
            "liquidity_buffer_pct": manager.liquidity_buffer_pct,
            "profit_benchmark_pct": manager.profit_benchmark_pct,
            "auto_rebalance": manager.auto_rebalance,
        },
    }


@app.post("/admin/liquidity")
@app.post("/api/admin/liquidity")
async def update_liquidity_settings(payload: LiquiditySettingsRequest):
    manager = get_liquidity_manager()

    if payload.liquidity_buffer_pct is not None:
        manager.liquidity_buffer_pct = payload.liquidity_buffer_pct
    if payload.profit_benchmark_pct is not None:
        manager.profit_benchmark_pct = payload.profit_benchmark_pct
    if payload.auto_rebalance is not None:
        manager.auto_rebalance = payload.auto_rebalance

    return {
        "status": "success",
        "message": "Liquidity settings updated",
        "settings": {
            "liquidity_buffer_pct": manager.liquidity_buffer_pct,
            "profit_benchmark_pct": manager.profit_benchmark_pct,
            "auto_rebalance": manager.auto_rebalance,
        },
    }


@app.post("/admin/liquidity/check-profit")
@app.post("/api/admin/liquidity/check-profit")
async def check_profit_benchmark(payload: ProfitBenchmarkRequest):
    manager = get_liquidity_manager()
    should_release, message = manager.check_profit_benchmark(
        payload.position_profit_pct
    )
    return {
        "status": "success",
        "should_release": should_release,
        "message": message,
        "current_profit": payload.position_profit_pct,
        "benchmark": manager.profit_benchmark_pct,
    }


@app.get("/procryon/health")
async def procryon_health():
    if ProcryonBot is None:
        raise HTTPException(status_code=503, detail=PROCRYON_IMPORT_ERROR)
    return get_procryon_bot().health_snapshot(
        attempt_broker_login=False,
        probe_fastapi=False,
    )


@app.get("/procryon/status")
async def procryon_status():
    if ProcryonBot is None:
        raise HTTPException(status_code=503, detail=PROCRYON_IMPORT_ERROR)
    return get_procryon_bot().status()


@app.post("/procryon/bootstrap")
async def procryon_bootstrap():
    if ProcryonBot is None:
        raise HTTPException(status_code=503, detail=PROCRYON_IMPORT_ERROR)
    bot = get_procryon_bot()
    return {
        "status": "bootstrapped",
        "metrics": bot.bootstrap_demo_models(),
    }


@app.post("/procryon/evaluate")
async def procryon_evaluate(payload: ProcryonEvaluateRequest):
    if ProcryonBot is None:
        raise HTTPException(status_code=503, detail=PROCRYON_IMPORT_ERROR)
    bot = get_procryon_bot()
    try:
        return bot.evaluate_opportunity(
            payload.spread_vector,
            payload.execution_features,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/procryon/configure")
async def procryon_configure(payload: ProcryonConfigureRequest):
    if ProcryonBot is None:
        raise HTTPException(status_code=503, detail=PROCRYON_IMPORT_ERROR)
    return get_procryon_bot().configure(payload.settings)


@app.get("/hydra/health")
async def hydra_health():
    if HydraBot is None:
        raise HTTPException(status_code=503, detail=HYDRA_IMPORT_ERROR)
    return get_hydra_bot().health_snapshot(probe_fastapi=False)


@app.get("/hydra/status")
async def hydra_status():
    if HydraBot is None:
        raise HTTPException(status_code=503, detail=HYDRA_IMPORT_ERROR)
    return get_hydra_bot().status()


@app.post("/hydra/bootstrap")
async def hydra_bootstrap():
    if HydraBot is None:
        raise HTTPException(status_code=503, detail=HYDRA_IMPORT_ERROR)
    bot = get_hydra_bot()
    return {
        "status": "bootstrapped",
        "analysis": bot.bootstrap_demo_state(),
    }


@app.post("/hydra/analyze")
async def hydra_analyze(payload: HydraAnalyzeRequest):
    if HydraBot is None:
        raise HTTPException(status_code=503, detail=HYDRA_IMPORT_ERROR)
    try:
        analysis = get_hydra_bot().analyze_ticker(
            payload.ticker,
            headlines=payload.news_headlines,
        )
        analysis["persistence"] = persist_hydra_analysis(
            analysis,
            airflow_dag_id=get_hydra_bot().config.airflow_dag_id,
        )
        return analysis
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/hydra/trade")
async def hydra_trade(payload: dict[str, Any]):
    if HydraBot is None:
        raise HTTPException(status_code=503, detail=HYDRA_IMPORT_ERROR)
    try:
        bot = get_hydra_bot()
        trade = bot.execute_trade(
            str(payload.get("broker", "")),
            str(payload.get("ticker", "")),
            str(payload.get("action", "")),
            qty=float(payload.get("qty", 0)),
            dry_run=bool(payload.get("dry_run", True)),
        )
        last_analysis = (
            bot.last_analysis
            if isinstance(bot.last_analysis, dict)
            else None
        )
        analysis_id = None
        if last_analysis:
            persistence = persist_hydra_analysis(
                last_analysis,
                airflow_dag_id=bot.config.airflow_dag_id,
            )
            analysis_id = persistence.get("analysis_id")
            trade["analysis_persistence"] = persistence
        trade["persistence"] = persist_hydra_trade_decision(
            trade,
            analysis=last_analysis,
            analysis_id=analysis_id,
        )
        _notify_bot_trade("Hydra", trade)
        return trade
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/hydra/configure")
async def hydra_configure(payload: HydraConfigureRequest):
    if HydraBot is None:
        raise HTTPException(status_code=503, detail=HYDRA_IMPORT_ERROR)
    return get_hydra_bot().configure(payload.settings)


@app.get("/hydra/airbyte-config")
async def hydra_airbyte_config():
    if HydraBot is None:
        raise HTTPException(status_code=503, detail=HYDRA_IMPORT_ERROR)
    return get_hydra_bot().airbyte_source_config()


@app.get("/triton/health")
async def triton_health():
    if TritonBot is None:
        raise HTTPException(status_code=503, detail=TRITON_IMPORT_ERROR)
    return get_triton_bot().health_snapshot()


@app.get("/triton/status")
async def triton_status():
    if TritonBot is None:
        raise HTTPException(status_code=503, detail=TRITON_IMPORT_ERROR)
    result = get_triton_bot().status()
    result["execution_enabled"] = _is_bot_active("Triton")
    return result


@app.post("/triton/bootstrap")
async def triton_bootstrap():
    if TritonBot is None:
        raise HTTPException(status_code=503, detail=TRITON_IMPORT_ERROR)
    bot = get_triton_bot()
    return {
        "status": "bootstrapped",
        "analysis": bot.bootstrap_demo_state(),
    }


@app.post("/triton/analyze")
async def triton_analyze(payload: TritonAnalyzeRequest):
    if TritonBot is None:
        raise HTTPException(status_code=503, detail=TRITON_IMPORT_ERROR)
    try:
        return get_triton_bot().analyze_ticker(
            payload.ticker,
            headlines=payload.news_headlines,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/triton/forecast")
async def triton_forecast(payload: TritonAnalyzeRequest):
    if TritonBot is None:
        raise HTTPException(status_code=503, detail=TRITON_IMPORT_ERROR)
    bot = get_triton_bot()
    try:
        history = bot._fetch_price_history(str(payload.ticker).strip().upper())
        return bot.arima_forecast(history)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/triton/trade")
async def triton_trade(payload: TritonTradeRequest):
    if TritonBot is None:
        raise HTTPException(status_code=503, detail=TRITON_IMPORT_ERROR)
    try:
        result = get_triton_bot().execute_trade(
            payload.broker,
            payload.ticker,
            payload.action,
            qty=payload.qty,
            dry_run=payload.dry_run,
        )
        _notify_bot_trade("Triton", result)
        return result
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/triton/configure")
async def triton_configure(payload: TritonConfigureRequest):
    if TritonBot is None:
        raise HTTPException(status_code=503, detail=TRITON_IMPORT_ERROR)
    return get_triton_bot().configure(payload.settings)


app.include_router(sentiment_router)
app.mount("/draco", draco_app)
app.mount("/vega", vega_app)


@app.get("/ibkr/health")
async def ibkr_health():
    client = get_ibkr_client()
    reachable = client.start_gateway()
    authenticated = client.check_auth_status() if reachable else False
    return {
        "reachable": reachable,
        "authenticated": authenticated,
        "account_id": client.config.account_id,
        "base_url": client.config.base_url,
    }


@app.get("/ibkr/ping")
async def ibkr_ping():
    """
    Diagnose CPAPI reachability across likely local URLs.

    This is intentionally verbose so same-day setup issues can be
    resolved fast.
    """
    configured = os.getenv(
        "IBKR_GATEWAY_URL",
        "https://localhost:5000",
    ).strip()

    candidates = []
    for url in [
        configured,
        "https://localhost:5000",
        "http://localhost:5000",
        "https://localhost:5001",
        "http://localhost:5001",
        "https://127.0.0.1:5000",
        "http://127.0.0.1:5000",
    ]:
        if url and url not in candidates:
            candidates.append(url)

    probes = [_probe_ibkr_auth_endpoint(u) for u in candidates]
    valid = [p for p in probes if p.get("ok")]

    guidance = []
    if not valid:
        guidance.append(
            "No valid IBKR CPAPI endpoint detected. Current "
            "localhost:5000 often maps to Docker in this workspace."
        )
        guidance.append(
            "Set IBKR_GATEWAY_URL to the actual Client Portal API URL, "
            "then restart API."
        )
        guidance.append(
            "Expected auth endpoint: <IBKR_GATEWAY_URL>/v1/api/iserver/"
            "auth/status returning JSON with authenticated field."
        )

    return {
        "configured_gateway_url": configured,
        "valid_endpoints": valid,
        "probes": probes,
        "guidance": guidance,
    }


@app.get("/ibkr/accounts")
async def ibkr_accounts():
    client = get_ibkr_client()
    if not client.start_gateway():
        raise HTTPException(
            status_code=503,
            detail="IBKR gateway unreachable",
        )
    accounts = client.get_accounts()
    if not accounts:
        raise HTTPException(
            status_code=502,
            detail="No IBKR accounts returned",
        )
    return {"accounts": accounts}


@app.post("/ibkr/forex/resolve")
async def ibkr_forex_resolve(payload: IBKRResolveForexRequest):
    client = get_ibkr_client()
    if not client.start_gateway():
        raise HTTPException(
            status_code=503,
            detail="IBKR gateway unreachable",
        )
    conid = client.resolve_forex_conid(
        payload.symbol,
        exchange=payload.exchange,
    )
    if conid is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Strict FOREX conid resolution failed; expected IDEALPRO CASH "
                "contract for symbol"
            ),
        )
    return {
        "symbol": payload.symbol,
        "exchange": payload.exchange,
        "conid": conid,
    }


@app.post("/ibkr/order")
async def ibkr_order(payload: IBKROrderRequest):
    client = get_ibkr_client()
    if not client.start_gateway():
        raise HTTPException(
            status_code=503,
            detail="IBKR gateway unreachable",
        )

    result: Any = client.place_order(
        conid=payload.conid,
        side=payload.side,
        quantity=payload.quantity,
        account_id=payload.account_id,
        order_type=payload.order_type,
        tif=payload.tif,
        price=payload.price,
    )
    if result is None:
        raise HTTPException(status_code=502, detail="IBKR order failed")

    return {
        "account_id": payload.account_id or client.config.account_id,
        "result": result,
    }


@app.post("/ibkr/forex/order")
async def ibkr_forex_order(payload: IBKRForexOrderRequest):
    client = get_ibkr_client()
    if not client.start_gateway():
        raise HTTPException(
            status_code=503,
            detail="IBKR gateway unreachable",
        )

    result: Any = client.place_forex_order(
        symbol=payload.symbol,
        side=payload.side,
        quantity=payload.quantity,
        account_id=payload.account_id,
        exchange=payload.exchange,
        order_type=payload.order_type,
        tif=payload.tif,
    )
    if result is None:
        raise HTTPException(status_code=502, detail="IBKR FOREX order failed")

    return {
        "account_id": payload.account_id or client.config.account_id,
        "symbol": payload.symbol,
        "result": result,
    }


@app.get("/ibkr/positions")
async def ibkr_positions(account_id: Optional[str] = Query(default=None)):
    client = get_ibkr_client()
    if not client.start_gateway():
        raise HTTPException(
            status_code=503,
            detail="IBKR gateway unreachable",
        )

    acct = account_id or client.config.account_id
    if not acct:
        raise HTTPException(
            status_code=400,
            detail="IBKR account_id is required",
        )

    result = client.api_request(f"/portfolio/{acct}/positions/0")
    if result is None:
        raise HTTPException(
            status_code=502,
            detail="IBKR positions request failed",
        )

    return {
        "account_id": acct,
        "positions": result,
    }
