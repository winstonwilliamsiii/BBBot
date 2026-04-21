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

try:
    from rhea_bot import RheaBot

    RHEA_IMPORT_ERROR = None
except (ImportError, OSError, RuntimeError, ValueError) as exc:
    RheaBot = None
    RHEA_IMPORT_ERROR = str(exc)

try:
    from altair_bot import app as altair_app
except (ImportError, OSError, RuntimeError, ValueError) as exc:
    altair_app = None
    ALTAIR_IMPORT_ERROR = str(exc)
else:
    ALTAIR_IMPORT_ERROR = None

from draco_bot import app as draco_app
from vega_bot import app as vega_app
from frontend.components.ibkr_gateway_client import (
    GatewayConfig,
    IBKRGatewayClient,
)
# discord_alpaca kept for backwards-compat with any direct callers in scripts/
# _discord_trade alias removed; _notify_bot_trade now uses discord_notify
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
        from frontend.utils.discord_notify import notify_trade
        side = str(trade_result.get("action") or trade_result.get("side") or "")
        notify_trade(
            bot_name=bot_name,
            symbol=str(trade_result.get("ticker", "")),
            side=side,
            qty=float(trade_result.get("qty", 0)),
            status=status,
            mode=str(trade_result.get("mode", "paper")),
            ticket=str(trade_result.get("order_id", "")) or None,
            broker=str(trade_result.get("broker", "")),
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


class RheaAnalyzeRequest(BaseModel):
    ticker: str = Field(min_length=1)
    news_headlines: list[str] = Field(default_factory=list)


class RheaTradeRequest(BaseModel):
    broker: str = Field(default="ibkr", min_length=1)
    ticker: str = Field(min_length=1)
    action: Literal["BUY", "SELL"]
    qty: float = Field(gt=0)
    dry_run: bool = True


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
def get_rhea_bot() -> Any:
    if RheaBot is None:
        raise RuntimeError(RHEA_IMPORT_ERROR or "Rhea unavailable")
    bot = RheaBot()
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


@app.get("/rhea/health")
async def rhea_health():
    if RheaBot is None:
        raise HTTPException(status_code=503, detail=RHEA_IMPORT_ERROR)
    return get_rhea_bot().health_snapshot(probe_fastapi=False)


@app.get("/rhea/status")
async def rhea_status():
    if RheaBot is None:
        raise HTTPException(status_code=503, detail=RHEA_IMPORT_ERROR)
    result = get_rhea_bot().status()
    result["execution_enabled"] = _is_bot_active("Rhea")
    return result


@app.post("/rhea/bootstrap")
async def rhea_bootstrap():
    if RheaBot is None:
        raise HTTPException(status_code=503, detail=RHEA_IMPORT_ERROR)
    return {
        "status": "bootstrapped",
        "analysis": get_rhea_bot().bootstrap_demo_state(),
    }


@app.post("/rhea/analyze")
async def rhea_analyze(payload: RheaAnalyzeRequest):
    if RheaBot is None:
        raise HTTPException(status_code=503, detail=RHEA_IMPORT_ERROR)
    try:
        return get_rhea_bot().analyze_ticker(
            payload.ticker,
            headlines=payload.news_headlines,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/rhea/trade")
async def rhea_trade(payload: RheaTradeRequest):
    if RheaBot is None:
        raise HTTPException(status_code=503, detail=RHEA_IMPORT_ERROR)
    try:
        result = get_rhea_bot().execute_trade(
            payload.broker,
            payload.ticker,
            payload.action,
            qty=payload.qty,
            dry_run=payload.dry_run,
        )
        _notify_bot_trade("Rhea", result)
        return result
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/rhea/airbyte-config")
async def rhea_airbyte_config():
    if RheaBot is None:
        raise HTTPException(status_code=503, detail=RHEA_IMPORT_ERROR)
    return get_rhea_bot().airbyte_source_config()


app.include_router(sentiment_router)
app.mount("/draco", draco_app)
app.mount("/vega", vega_app)
if altair_app is not None:
    app.mount("/altair", altair_app)

# ── Cosmic Signal Router ──────────────────────────────────────────────────────
try:
    from frontend.utils.cosmic_signal import (
        compute_cosmic_score,
        get_engine as _get_cosmic_engine,

        HEAD_MOMENTUM, HEAD_RSI, HEAD_SENTIMENT, HEAD_VOLATILITY,
        HEAD_LIQUIDITY, HEAD_ML_CONF, HEAD_SPREAD, HEAD_MULTIFRAME,
    )
    COSMIC_AVAILABLE = True
except Exception as _cosmic_exc:
    COSMIC_AVAILABLE = False
    _COSMIC_IMPORT_ERROR = str(_cosmic_exc)

# Known bots and their strategy metadata
_BOT_SIGNAL_META: dict[str, dict] = {
    "Titan":    {"fund": "Mansa Tech",         "strategy": "CNN Deep Learning"},
    "Vega":     {"fund": "Mansa Retail",        "strategy": "MTF-ML"},
    "Rigel":    {"fund": "Mansa FOREX",         "strategy": "Mean Reversion"},
    "Dogon":    {"fund": "Mansa ETF",           "strategy": "Portfolio Optimizer"},
    "Orion":    {"fund": "Mansa Minerals",      "strategy": "GoldRSI Strategy"},
    "Draco":    {"fund": "Mansa Money Bag",     "strategy": "Sentiment Analyzer"},
    "Altair":   {"fund": "Mansa AI Fund",       "strategy": "News Trading"},
    "Procryon": {"fund": "Mansa Crypto Fund",   "strategy": "Crypto Spread Arbitrage"},
    "Hydra":    {"fund": "Mansa Health",        "strategy": "Momentum Strategy"},
    "Triton":   {"fund": "Mansa Transportation", "strategy": "Pending"},
    "Dione":    {"fund": "Mansa Options",       "strategy": "Put Call Parity"},
    "Cephei":   {"fund": "Mansa Cephei",        "strategy": "Volatility Arb"},
    "Rhea":     {"fund": "Mansa ADI",           "strategy": "Intra-Day / Swing"},
    "Jupicita": {"fund": "Mansa Smalls",        "strategy": "Pairs Trading"},
}

_VALID_BOTS = sorted(_BOT_SIGNAL_META.keys())


class CosmicEvaluateRequest(BaseModel):
    """Input payload for POST /signals/evaluate."""
    context:  dict[str, Any] = Field(default_factory=dict)
    symbol:   Optional[str] = None
    bot_name: Optional[str] = None
    mode:     str = "paper"


@app.get("/signals/heads")
@app.get("/api/signals/heads")
async def signals_heads_info():
    """Return the list of analytic heads, their default weights, and purpose."""
    if not COSMIC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Cosmic signal engine unavailable")
    from frontend.utils.cosmic_signal import DEFAULT_WEIGHTS
    heads = [
        {"head": HEAD_MOMENTUM,   "weight": DEFAULT_WEIGHTS[HEAD_MOMENTUM],   "purpose": "Short-term price momentum direction"},
        {"head": HEAD_RSI,        "weight": DEFAULT_WEIGHTS[HEAD_RSI],        "purpose": "RSI overbought/oversold reversal signal"},
        {"head": HEAD_SENTIMENT,  "weight": DEFAULT_WEIGHTS[HEAD_SENTIMENT],  "purpose": "News/market sentiment overlay"},
        {"head": HEAD_VOLATILITY, "weight": DEFAULT_WEIGHTS[HEAD_VOLATILITY], "purpose": "Bollinger bandwidth / volatility gate"},
        {"head": HEAD_LIQUIDITY,  "weight": DEFAULT_WEIGHTS[HEAD_LIQUIDITY],  "purpose": "Cash-to-equity liquidity guardrail"},
        {"head": HEAD_ML_CONF,    "weight": DEFAULT_WEIGHTS[HEAD_ML_CONF],    "purpose": "ML model probability directional vote"},
        {"head": HEAD_SPREAD,     "weight": DEFAULT_WEIGHTS[HEAD_SPREAD],     "purpose": "Execution quality (spread / slippage)"},
        {"head": HEAD_MULTIFRAME, "weight": DEFAULT_WEIGHTS[HEAD_MULTIFRAME], "purpose": "Cross-timeframe alignment score"},
    ]
    return {
        "heads": heads,
        "thresholds": {
            "buy_threshold": 0.20,
            "sell_threshold": -0.20,
        },
        "decisions": {
            "BUY":  "🔥 starfire  — positive cosmic alignment",
            "SELL": "🌑 eclipse   — negative cosmic alignment",
            "HOLD": "⚖️  cosmic balance — neutral zone",
        },
    }


@app.get("/signals/cosmic")
@app.get("/api/signals/cosmic")
async def signals_cosmic(
    symbol: Optional[str] = Query(default=None),
    bot_name: Optional[str] = Query(default=None),
    mode: str = Query(default="paper"),
    rsi: float = Query(default=50.0),
    momentum: float = Query(default=0.0),
    sentiment_score: float = Query(default=0.0),
    volatility_bandwidth: float = Query(default=0.5),
    liquidity_ratio: float = Query(default=0.5),
    execution_probability: float = Query(default=0.5),
    predicted_side: str = Query(default="buy"),
    average_spread_bps: float = Query(default=20.0),
):
    """Evaluate the Cosmic Score from query-parameter inputs.

    Returns the full analytic head breakdown plus the braided decision
    (BUY 🔥 starfire / SELL 🌑 eclipse / HOLD ⚖️ cosmic balance).
    """
    if not COSMIC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Cosmic signal engine unavailable")

    ctx = {
        "rsi": rsi,
        "momentum": momentum,
        "sentiment_score": sentiment_score,
        "volatility_bandwidth": volatility_bandwidth,
        "liquidity_ratio": liquidity_ratio,
        "execution_probability": execution_probability,
        "predicted_side": predicted_side,
        "average_spread_bps": average_spread_bps,
    }
    snap = compute_cosmic_score(ctx, symbol=symbol, bot_name=bot_name, mode=mode)
    return snap.to_dict()


@app.post("/signals/evaluate")
@app.post("/api/signals/evaluate")
async def signals_evaluate(payload: CosmicEvaluateRequest):
    """Evaluate Cosmic Score from a full market-context payload.

    Accepts any combination of the recognised signal keys; unknown keys are
    forwarded as-is for custom head logic.
    """
    if not COSMIC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Cosmic signal engine unavailable")
    snap = compute_cosmic_score(
        payload.context,
        symbol=payload.symbol,
        bot_name=payload.bot_name,
        mode=payload.mode,
    )
    return snap.to_dict()


@app.get("/signals/{bot_name}")
@app.get("/api/signals/{bot_name}")
async def signals_for_bot(
    bot_name: str,
    mode: str = Query(default="paper"),
):
    """Return the last cached Cosmic Signal snapshot for a specific bot.

    If no evaluation has been cached yet, returns a neutral demo snapshot
    using each bot's live telemetry where available.
    """
    if not COSMIC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Cosmic signal engine unavailable")

    canonical = next(
        (b for b in _VALID_BOTS if b.lower() == bot_name.lower()), None
    )
    if canonical is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown bot '{bot_name}'. Valid bots: {_VALID_BOTS}",
        )

    engine = _get_cosmic_engine()
    snap = engine.last_snapshot(bot_name=canonical)

    if snap is None:
        # Build a representative context from live bot telemetry where possible
        ctx: dict[str, Any] = {}

        if canonical == "Procryon" and ProcryonBot is not None:
            try:
                bot = get_procryon_bot()
                eval_r = bot.evaluate_opportunity(
                    spread_vector=[0.0, 0.0, 0.0],
                    execution_features=[0.0, 0.0, 0.0, 0.0, 0.0],
                )
                ctx["execution_probability"] = float(eval_r.get("execution_probability", 0.5))
                ctx["predicted_side"] = "buy" if eval_r.get("execute") else "sell"
                ctx["average_spread_bps"] = float(eval_r.get("average_spread_bps", 20.0))
            except Exception:
                pass

        elif canonical in ("Hydra", "Triton") and HydraBot is not None:
            try:
                bot_obj = get_hydra_bot() if canonical == "Hydra" else get_triton_bot()
                analysis = bot_obj.analyze("SPY", [])
                ctx["sentiment_score"] = float(analysis.get("sentiment_score", 0.0))
                ctx["execution_probability"] = float(analysis.get("prediction_probability", 0.5))
            except Exception:
                pass

        snap = engine.evaluate(ctx, symbol=None, bot_name=canonical, mode=mode, force=True)

    meta = _BOT_SIGNAL_META.get(canonical, {})
    result = snap.to_dict()
    result["bot_meta"] = meta
    return result


@app.get("/signals")
@app.get("/api/signals")
async def signals_all(mode: str = Query(default="paper")):
    """Return a summary of Cosmic Scores across all known bots.

    Bots not yet evaluated return a neutral snapshot.
    """
    if not COSMIC_AVAILABLE:
        raise HTTPException(status_code=503, detail="Cosmic signal engine unavailable")

    from frontend.utils.cosmic_signal import compute_cosmic_score as _ccs

    engine = _get_cosmic_engine()
    results = []
    for bot in _VALID_BOTS:
        snap = engine.last_snapshot(bot_name=bot)
        if snap is None:
            snap = _ccs({}, bot_name=bot, mode=mode)
        meta = _BOT_SIGNAL_META.get(bot, {})
        results.append({
            "bot_name":     bot,
            "fund":         meta.get("fund", ""),
            "strategy":     meta.get("strategy", ""),
            "cosmic_score": snap.cosmic_score,
            "decision":     snap.decision,
            "cosmic_symbol": snap.cosmic_symbol,
            "timestamp":    snap.timestamp,
            "mode":         snap.mode,
        })

    return {
        "signals": results,
        "total":   len(results),
        "buy_count":  sum(1 for r in results if r["decision"] == "BUY"),
        "sell_count": sum(1 for r in results if r["decision"] == "SELL"),
        "hold_count": sum(1 for r in results if r["decision"] == "HOLD"),
    }


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
