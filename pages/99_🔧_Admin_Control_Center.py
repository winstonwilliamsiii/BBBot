"""
🔧 Bentley Bot Control Center - Admin Dashboard

Internal admin interface for:
- Bot deployment and monitoring
- Broker health and orchestration
- Prop firm execution management
- Risk engine controls
- System monitoring

**Access:** Internal admin only
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from typing import Literal
import json
import subprocess
import sys
import os
from pathlib import Path
from urllib.parse import urlparse

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from bbbot1_pipeline.mlflow_config import (
        get_mlflow_tracking_uri,
        get_mlflow_server_url,
        get_mlflow_backend_store_uri,
    )
except Exception:
    def get_mlflow_tracking_uri():
        return os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

    def get_mlflow_server_url():
        return os.getenv("MLFLOW_SERVER_URL", "http://localhost:5000")

    def get_mlflow_backend_store_uri():
        return os.getenv("MLFLOW_BACKEND_STORE_URI", "not-configured")

try:
    from frontend.utils.bot_fund_mapping import get_bot_catalog_rows
except Exception:
    def get_bot_catalog_rows():
        return [
            {
                "bot": "Titan",
                "fund": "Mansa Tech",
                "strategy": "CNN with Deep Learning",
            },
            {
                "bot": "Vega_Bot",
                "fund": "Mansa_Retail",
                "strategy": "Vega Mansa Retail MTF-ML",
            },
            {"bot": "Draco", "fund": "Mansa Money Bag", "strategy": "Sentiment Analyzer"},
            {"bot": "Altair", "fund": "Mansa AI", "strategy": "News Trading"},
            {"bot": "Procryon", "fund": "Crypto Fund", "strategy": "Crypto Arbitrage"},
            {"bot": "Hydra", "fund": "Mansa Health", "strategy": "Momentum Strategy"},
            {
                "bot": "Triton",
                "fund": "Mansa Transportation",
                "strategy": "Pending",
            },
            {
                "bot": "Dione",
                "fund": "Mansa Options",
                "strategy": "Put Call Parity",
            },
            {"bot": "Dogon", "fund": "Mansa ETF", "strategy": "Portfolio Optimizer"},
            {"bot": "Rigel", "fund": "Mansa FOREX", "strategy": "Mean Reversion"},
            {"bot": "Orion", "fund": "Mansa Minerals", "strategy": "GoldRSI Strategy"},
            {"bot": "Rhea", "fund": "Mansa ADI", "strategy": "Intra-Day / Swing"},
            {
                "bot": "Jupicita",
                "fund": "Mansa_Smalls",
                "strategy": "Pairs Trading",
            },
        ]

try:
    from config.broker_mode_config import get_config as get_broker_mode_config
except Exception:
    get_broker_mode_config = None

try:
    from frontend.utils.rbac import RBACManager, UserRole
    RBAC_AVAILABLE = True
except Exception:
    RBAC_AVAILABLE = False

# Configuration
DEFAULT_CONTROL_CENTER_URL = os.getenv("CONTROL_CENTER_API_URL", "http://localhost:5001")
DEFAULT_MLFLOW_TRACKING_URI = get_mlflow_tracking_uri()
DEFAULT_MLFLOW_URL = get_mlflow_server_url()
MLFLOW_BENCHMARK_BOTS = ["Titan", "Orion", "Rigel", "Dogon"]
TITAN_MLFLOW_SCHEMA_ROWS = [
    {
        "Category": "Experiment Tracking",
        "Field": "params.feature_schema_version",
        "Kind": "param",
        "Purpose": "Version the Titan CNN/ensemble feature contract.",
    },
    {
        "Category": "Experiment Tracking",
        "Field": "metrics.titan_rsi_cycle_current",
        "Kind": "metric",
        "Purpose": "Latest RSI value used to ground timing discipline.",
    },
    {
        "Category": "Experiment Tracking",
        "Field": "metrics.titan_rsi_cycle_span",
        "Kind": "metric",
        "Purpose": "Oscillation width across the recent RSI cycle window.",
    },
    {
        "Category": "Experiment Tracking",
        "Field": "metrics.titan_volatility_bandwidth",
        "Kind": "metric",
        "Purpose": "Current Bollinger bandwidth used for volatility gating.",
    },
    {
        "Category": "Experiment Tracking",
        "Field": "metrics.titan_sentiment_score",
        "Kind": "metric",
        "Purpose": "Sentiment overlay from WSJ/Airbyte-style feeds.",
    },
    {
        "Category": "Experiment Tracking",
        "Field": "metrics.titan_liquidity_ratio",
        "Kind": "metric",
        "Purpose": "Cash-to-equity guardrail before execution.",
    },
    {
        "Category": "Metrics Logging",
        "Field": "metrics.titan_effective_liquidity_buffer",
        "Kind": "metric",
        "Purpose": "Final liquidity threshold after sentiment adjustment.",
    },
    {
        "Category": "Metrics Logging",
        "Field": "metrics.titan_liquidity_buffer_adjustment",
        "Kind": "metric",
        "Purpose": "How much sentiment tightened or loosened the buffer.",
    },
    {
        "Category": "Metrics Logging",
        "Field": "metrics.titan_prediction_probability",
        "Kind": "metric",
        "Purpose": "Trade-success probability produced by the ensemble.",
    },
    {
        "Category": "Metrics Logging",
        "Field": "metrics.titan_prediction_confidence",
        "Kind": "metric",
        "Purpose": "Confidence score for forensic review and ranking.",
    },
    {
        "Category": "Guard Outcome",
        "Field": "tags.trade_status",
        "Kind": "tag",
        "Purpose": "Approved, simulated, blocked, or error decision outcome.",
    },
    {
        "Category": "Model Registry",
        "Field": "params.model_registry_uri",
        "Kind": "param",
        "Purpose": "Registry alias used for Titan model promotion.",
    },
    {
        "Category": "Artifacts",
        "Field": "titan_decision_context.json",
        "Kind": "artifact",
        "Purpose": "Feature snapshot and decision context for replay.",
    },
]


def probe_mlflow_server(base_url: str):
    """Probe MLflow endpoint and return (confirmed, host_reachable, note)."""
    checks = [
        ("GET", "/health", None),
        ("GET", "/version", None),
        ("POST", "/api/2.0/mlflow/experiments/search", {"max_results": 1}),
        ("GET", "/", None),
    ]

    host_reachable = False

    for method, path, payload in checks:
        try:
            url = f"{base_url}{path}"
            if method == "POST":
                response = requests.post(url, json=payload, timeout=3)
            else:
                response = requests.get(url, timeout=3)

            status = response.status_code
            if status < 500:
                host_reachable = True

            if path in ("/health", "/version") and status == 200:
                return True, host_reachable, f"MLflow endpoint {path} responded with HTTP {status}."

            if path == "/api/2.0/mlflow/experiments/search" and status in (200, 400, 401, 403):
                return True, host_reachable, "MLflow REST API is reachable."

            if path == "/" and status == 200 and "mlflow" in response.text.lower():
                return True, host_reachable, "MLflow UI page responded successfully."

        except requests.exceptions.RequestException:
            continue

    return False, host_reachable, "No MLflow endpoints were detected at this URL."


def _first_present(row, candidates):
    for candidate in candidates:
        if candidate in row and pd.notna(row[candidate]):
            return row[candidate]
    return None


def _infer_bot_name_from_run(row) -> str:
    values = [
        _first_present(
            row,
            [
                "tags.bot",
                "params.active_bot",
                "params.bot_name",
                "params.bot",
                "experiment_name",
            ],
        )
    ]

    normalized_values = [str(value).strip().lower() for value in values if value]
    for value in normalized_values:
        if "titan" in value:
            return "Titan"
        if "orion" in value:
            return "Orion"
        if "rigel" in value:
            return "Rigel"
        if "dogon" in value:
            return "Dogon"
    return "Other"


def _extract_trade_status(row) -> str:
    status = _first_present(row, ["tags.trade_status", "status"])
    if status is None:
        return "unknown"
    return str(status)


def _extract_prediction_confidence(row) -> float | None:
    confidence = _first_present(row, ["metrics.titan_prediction_confidence"])
    if confidence is not None:
        return float(confidence)

    probability = _first_present(row, ["metrics.titan_prediction_probability"])
    label = _first_present(row, ["metrics.titan_prediction_label"])
    if probability is None:
        return None

    probability = float(probability)
    if label is None:
        return max(probability, 1.0 - probability)
    return probability if float(label) >= 0.5 else (1.0 - probability)


def build_mlflow_benchmark_frame(runs_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if runs_df.empty:
        return pd.DataFrame()

    working = runs_df.copy()
    working["benchmark_bot"] = working.apply(_infer_bot_name_from_run, axis=1)
    working["trade_status_value"] = working.apply(_extract_trade_status, axis=1)
    working["prediction_confidence"] = working.apply(
        _extract_prediction_confidence,
        axis=1,
    )

    for bot_name in MLFLOW_BENCHMARK_BOTS:
        bot_runs = working[working["benchmark_bot"] == bot_name].copy()
        if bot_runs.empty:
            rows.append(
                {
                    "Bot": bot_name,
                    "Discipline": (
                        "ML-driven discipline"
                        if bot_name == "Titan"
                        else "Raw strategy"
                    ),
                    "Runs": 0,
                    "Avg Probability": None,
                    "Avg Confidence": None,
                    "Blocked Rate": None,
                    "Latest Status": "no-mlflow-runs",
                    "Last Updated": "N/A",
                }
            )
            continue

        probability = pd.to_numeric(
            bot_runs.get("metrics.titan_prediction_probability"),
            errors="coerce",
        )
        confidence = pd.to_numeric(
            bot_runs.get("prediction_confidence"),
            errors="coerce",
        )
        statuses = bot_runs["trade_status_value"].astype(str).str.lower()
        blocked_rate = statuses.str.startswith("blocked").mean()
        last_updated = "N/A"
        if "start_time" in bot_runs.columns:
            timestamp = pd.to_datetime(bot_runs["start_time"], errors="coerce").max()
            if pd.notna(timestamp):
                last_updated = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        rows.append(
            {
                "Bot": bot_name,
                "Discipline": (
                    "ML-driven discipline"
                    if bot_name == "Titan"
                    else "Raw strategy"
                ),
                "Runs": int(len(bot_runs)),
                "Avg Probability": (
                    round(float(probability.dropna().mean()), 4)
                    if probability is not None and not probability.dropna().empty
                    else None
                ),
                "Avg Confidence": (
                    round(float(confidence.dropna().mean()), 4)
                    if not confidence.dropna().empty
                    else None
                ),
                "Blocked Rate": (
                    round(float(blocked_rate), 4)
                    if len(statuses)
                    else None
                ),
                "Latest Status": str(statuses.iloc[0]) if len(statuses) else "unknown",
                "Last Updated": last_updated,
            }
        )

    return pd.DataFrame(rows)


def build_titan_forensic_frame(runs_df: pd.DataFrame) -> pd.DataFrame:
    if runs_df.empty:
        return pd.DataFrame()

    working = runs_df.copy()
    working["benchmark_bot"] = working.apply(_infer_bot_name_from_run, axis=1)
    titan_runs = working[working["benchmark_bot"] == "Titan"].copy()
    if titan_runs.empty:
        return pd.DataFrame()

    titan_runs["status"] = titan_runs.apply(_extract_trade_status, axis=1)
    titan_runs["confidence"] = titan_runs.apply(_extract_prediction_confidence, axis=1)

    columns = {
        "start_time": "Start Time",
        "params.symbol": "Symbol",
        "params.side": "Side",
        "status": "Decision",
        "metrics.titan_prediction_probability": "Probability",
        "confidence": "Confidence",
        "metrics.titan_rsi_cycle_current": "RSI",
        "metrics.titan_sentiment_score": "Sentiment",
        "metrics.titan_liquidity_ratio": "Liquidity Ratio",
        "metrics.titan_effective_liquidity_buffer": "Liquidity Buffer",
        "metrics.titan_liquidity_buffer_adjustment": "Buffer Delta",
    }
    available = {key: value for key, value in columns.items() if key in titan_runs.columns}
    if not available:
        return pd.DataFrame()

    forensic = titan_runs[list(available.keys())].copy().rename(columns=available)
    if "Start Time" in forensic.columns:
        parsed = pd.to_datetime(forensic["Start Time"], errors="coerce")
        forensic["Start Time"] = parsed.dt.strftime("%Y-%m-%d %H:%M:%S")
    return forensic.head(12)


def build_model_registry_frame(client) -> pd.DataFrame:
    try:
        models = list(client.search_registered_models(max_results=50))
    except TypeError:
        models = list(client.search_registered_models())
    except Exception:
        return pd.DataFrame()

    rows = []
    for model in models:
        latest_versions = getattr(model, "latest_versions", None) or []
        if latest_versions:
            for version in latest_versions:
                rows.append(
                    {
                        "Model": model.name,
                        "Version": str(getattr(version, "version", "")),
                        "Stage": str(getattr(version, "current_stage", "")),
                        "Run ID": str(getattr(version, "run_id", "")),
                        "Source": str(getattr(version, "source", "")),
                    }
                )
        else:
            rows.append(
                {
                    "Model": model.name,
                    "Version": "",
                    "Stage": "",
                    "Run ID": "",
                    "Source": "",
                }
            )

    return pd.DataFrame(rows)


def _append_unique_url(candidate_urls, base_url: str):
    """Append a URL candidate once, preserving order."""
    if base_url and base_url not in candidate_urls:
        candidate_urls.append(base_url)


def _swap_loopback_host(base_url: str, replacement_host: str) -> str | None:
    """Swap localhost and 127.0.0.1 for Windows loopback fallback checks."""
    parsed = urlparse(base_url)
    if parsed.scheme.lower() not in ("http", "https"):
        return None

    hostname = parsed.hostname or ""
    if hostname not in ("localhost", "127.0.0.1") or hostname == replacement_host:
        return None

    auth = ""
    if parsed.username:
        auth = parsed.username
        if parsed.password:
            auth = f"{auth}:{parsed.password}"
        auth = f"{auth}@"

    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path or ""
    query = f"?{parsed.query}" if parsed.query else ""
    fragment = f"#{parsed.fragment}" if parsed.fragment else ""
    return f"{parsed.scheme}://{auth}{replacement_host}{port}{path}{query}{fragment}"


def resolve_mlflow_server_url():
    """Resolve a reachable MLflow server URL with loopback fallbacks."""
    cached_url = st.session_state.get("resolved_mlflow_server_url")
    cached_note = st.session_state.get("resolved_mlflow_server_note")
    if cached_url:
        return cached_url, cached_note or "Using cached MLflow server resolution."

    candidate_urls = []
    _append_unique_url(candidate_urls, DEFAULT_MLFLOW_URL)
    _append_unique_url(candidate_urls, _swap_loopback_host(DEFAULT_MLFLOW_URL, "127.0.0.1"))
    _append_unique_url(candidate_urls, _swap_loopback_host(DEFAULT_MLFLOW_URL, "localhost"))
    _append_unique_url(candidate_urls, "http://127.0.0.1:5000")
    _append_unique_url(candidate_urls, "http://localhost:5000")

    last_note = "No MLflow endpoints were detected at the configured URL."
    for base_url in candidate_urls:
        connected, _, probe_note = probe_mlflow_server(base_url)
        if connected:
            st.session_state.resolved_mlflow_server_url = base_url
            st.session_state.resolved_mlflow_server_note = probe_note
            return base_url, probe_note
        last_note = probe_note

    st.session_state.resolved_mlflow_server_url = DEFAULT_MLFLOW_URL
    st.session_state.resolved_mlflow_server_note = last_note
    return DEFAULT_MLFLOW_URL, last_note


def get_resolved_mlflow_tracking_uri() -> str:
    """Use the resolved MLflow server URL for HTTP tracking URIs."""
    tracking_uri = DEFAULT_MLFLOW_TRACKING_URI
    if urlparse(tracking_uri).scheme.lower() in ("http", "https"):
        resolved_url, _ = resolve_mlflow_server_url()
        return resolved_url
    return tracking_uri


def resolve_control_center_api_url():
    """Resolve a reachable Control Center API URL with localhost fallbacks."""
    cached_url = st.session_state.get("resolved_control_center_api_url")
    if cached_url:
        return cached_url

    candidate_urls = [DEFAULT_CONTROL_CENTER_URL]
    if DEFAULT_CONTROL_CENTER_URL != "http://localhost:5001":
        candidate_urls.append("http://localhost:5001")
    if DEFAULT_CONTROL_CENTER_URL != "http://localhost:5000":
        candidate_urls.append("http://localhost:5000")

    for base_url in candidate_urls:
        try:
            response = requests.get(f"{base_url}/health", timeout=1.5)
            if response.status_code == 200:
                st.session_state.resolved_control_center_api_url = base_url
                return base_url
        except requests.exceptions.RequestException:
            continue

    st.session_state.resolved_control_center_api_url = DEFAULT_CONTROL_CENTER_URL
    return DEFAULT_CONTROL_CENTER_URL


def show_control_center_api_notice_once(reason: str = "unavailable"):
    """Show a single non-blocking notice when API data cannot be loaded."""
    if st.session_state.get("control_center_api_notice_shown"):
        return

    configured_url = st.session_state.get(
        "resolved_control_center_api_url",
        DEFAULT_CONTROL_CENTER_URL,
    )
    st.warning(
        (
            f"Control Center API is {reason} at {configured_url}. "
            "Showing fallback data where available."
        )
    )
    st.info(
        "Start the API with: `powershell -ExecutionPolicy Bypass "
        "-File .\\start_control_center_api.ps1`"
    )
    st.session_state.control_center_api_notice_shown = True

# Page config
st.set_page_config(
    page_title="Bentley Bot Control Center",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at top left, #111827 0%, #0b1220 55%, #030712 100%);
        color: #ffffff;
    }
    [data-testid="stHeader"], [data-testid="stSidebar"] {
        background: #0b1220;
    }
    [data-testid="stSidebar"] {
        border-right: 1px solid #1f2937;
    }
    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] *,
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] *,
    [data-testid="stMetricDelta"],
    [data-testid="stMetricDelta"] *,
    [data-testid="stCaptionContainer"] *,
    [data-testid="stMarkdownContainer"] *,
    p,
    span,
    div,
    li,
    label,
    td,
    th,
    small {
        color: #ffffff !important;
        opacity: 1 !important;
    }
    .metric-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-sizing: border-box;
    }
    .status-healthy { color: #10b981; font-weight: bold; }
    .status-warning { color: #f59e0b; font-weight: bold; }
    .status-error { color: #ef4444; font-weight: bold; }
    .control-button {
        background: #3b82f6;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        border: none;
        cursor: pointer;
    }
    .section-header {
        background: #111827;
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0 10px 0;
        border: 1px solid #374151;
    }
</style>
""", unsafe_allow_html=True)


# Authentication Check
def check_admin_auth():
    """Verify admin authentication."""
    if RBAC_AVAILABLE:
        RBACManager.init_session_state()
        current_user = RBACManager.get_current_user()
        if current_user and current_user.role == UserRole.ADMIN:
            st.session_state.admin_authenticated = True
            st.session_state.admin_user = current_user.username
            return True

    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        st.warning("🔒 Admin authentication required")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.subheader("Admin Login")
            username = st.text_input("Username", key="admin_username")
            password = st.text_input("Password", type="password", key="admin_password")
            
            if st.button("Login", type="primary"):
                if RBAC_AVAILABLE and RBACManager.login(username, password):
                    current_user = RBACManager.get_current_user()
                    if current_user and current_user.role == UserRole.ADMIN:
                        st.session_state.admin_authenticated = True
                        st.session_state.admin_user = current_user.username
                        st.rerun()
                    RBACManager.logout()
                    st.error("Admin role required")
                elif username == "admin" and password == "admin":  # Legacy DEVELOPMENT ONLY
                    st.session_state.admin_authenticated = True
                    st.session_state.admin_user = username
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        return False
    return True


# Helper Functions
def api_request(endpoint, method="GET", data=None, show_notice=False):
    """Make request to the Control Center FastAPI service."""
    try:
        control_center_api_url = resolve_control_center_api_url()
        normalized = endpoint if str(endpoint).startswith("/") else f"/{endpoint}"
        endpoint_variants = [normalized]

        # The unified FastAPI app accepts both `/admin/*` and `/api/admin/*`
        # so older UI paths continue to work.
        if normalized.startswith("/api/"):
            endpoint_variants.append(normalized[4:])
        elif normalized.startswith("/admin/"):
            endpoint_variants.append(f"/api{normalized}")

        last_status = None
        for path in endpoint_variants:
            url = f"{control_center_api_url}{path}"
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=5)
            elif method == "DELETE":
                response = requests.delete(url, timeout=5)
            else:
                return None

            last_status = response.status_code
            if response.status_code == 200:
                return response.json()

            # Try alternate route shape before surfacing non-connectivity notice.
            if response.status_code in (404, 405):
                continue

            if show_notice:
                show_control_center_api_notice_once(
                    f"returning HTTP {response.status_code}"
                )
            return None

        # All route variants were not implemented; rely on page fallback data silently.
        if last_status in (404, 405):
            return None

        if show_notice:
            show_control_center_api_notice_once(
                f"returning HTTP {last_status or 'unknown'}"
            )
        return None
    except requests.exceptions.ConnectionError:
        if show_notice:
            show_control_center_api_notice_once("unreachable")
        return None
    except Exception:
        if show_notice:
            show_control_center_api_notice_once("temporarily unavailable")
        return None


BOT_DEFAULT_BROKERS = {
    "Titan": "ALPACA",
    "Vega": "IBKR",
    "Rigel": "ALPACA",
    "Dogon": "ALPACA",
    "Orion": "ALPACA",
    "Hydra": "ALPACA",
    "Triton": "ALPACA",
}


def get_bot_default_broker(bot_name: str) -> str:
    return BOT_DEFAULT_BROKERS.get(str(bot_name or "").strip(), "AUTO")


def get_hydra_control_snapshot() -> dict:
    return {
        "status": api_request("/hydra/status", show_notice=False) or {},
        "health": api_request("/hydra/health", show_notice=False) or {},
    }


def get_triton_control_snapshot() -> dict:
    return {
        "status": api_request("/triton/status", show_notice=False) or {},
        "health": api_request("/triton/health", show_notice=False) or {},
    }


def get_status_badge(status):
    """Return colored status badge."""
    if status in ["running", "healthy", "active"]:
        return f'<span class="status-healthy">● {status.upper()}</span>'
    elif status in ["warning", "degraded", "idle"]:
        return f'<span class="status-warning">● {status.upper()}</span>'
    else:
        return f'<span class="status-error">● {status.upper()}</span>'


def probe_http_service(
    base_url: str,
    probe_paths: list[str] | None = None,
) -> tuple[str, str]:
    """Probe a local HTTP service and return (status, note)."""
    paths = probe_paths or ["/"]
    saw_timeout = False
    saw_server_error = False

    for path in paths:
        try:
            response = requests.get(
                f"{base_url}{path}",
                timeout=3,
                allow_redirects=True,
            )
            if response.status_code == 200:
                return "healthy", f"Reachable at {path} (HTTP 200)."
            if response.status_code < 500:
                return (
                    "warning",
                    f"Reachable at {path} (HTTP {response.status_code}).",
                )
            saw_server_error = True
        except requests.exceptions.Timeout:
            saw_timeout = True
        except requests.exceptions.RequestException:
            continue

    if saw_timeout:
        return "warning", "Timed out while probing the local endpoint."
    if saw_server_error:
        return "warning", "Service responded with a server-side error."
    return "error", "Service is not responding on localhost."


def get_service_dashboard_entries(
    local_services: list[dict] | None = None,
) -> list[dict]:
    """Return service dashboard cards for the admin UI."""
    docker_index = {
        service["name"]: service for service in (local_services or [])
    }
    resolved_mlflow_url, resolved_probe_note = resolve_mlflow_server_url()
    definitions = [
        {
            "name": "Airflow",
            "icon": "📊",
            "url": "http://localhost:8080",
            "button": "Open Airflow UI",
            "description": "Workflow orchestration and scheduled DAG runs.",
            "details": "DAGs: /workflows/airflow/dags/",
            "credentials": "admin / admin",
            "probe_paths": ["/health", "/"],
        },
        {
            "name": "MLflow",
            "icon": "🧠",
            "url": resolved_mlflow_url,
            "button": "Open MLflow UI",
            "description": "Experiment tracking and model run history.",
            "details": "Tracking URI resolved dynamically from local config.",
            "probe": "mlflow",
        },
        {
            "name": "KNIME",
            "icon": "📈",
            "button": "Managed Through Airflow",
            "description": "Visual analytics workflows executed through DAGs.",
            "details": "Workflows: /workflows/knime/dags/",
            "status": "healthy",
            "note": "KNIME jobs are integrated through Airflow orchestration.",
        },
        {
            "name": "Streamlit",
            "icon": "💰",
            "url": "http://localhost:8501",
            "button": "Open Budget Dashboard",
            "description": (
                "Portfolio, budget, and admin interface entrypoint."
            ),
            "details": "Main UI entry: streamlit_app.py",
            "probe_paths": ["/_stcore/health", "/"],
        },
        {
            "name": "Airbyte",
            "icon": "🔄",
            "url": "http://localhost:8000",
            "button": "Open Airbyte UI",
            "description": "Data ingestion and ETL pipeline management.",
            "details": "Workflows: /workflows/airbyte/dags/",
            "probe_paths": ["/api/v1/health", "/"],
        },
    ]

    entries = []
    for definition in definitions:
        status = definition.get("status", "error")
        note = definition.get("note", "Status unavailable.")

        if definition.get("probe") == "mlflow":
            connected, host_reachable, probe_note = probe_mlflow_server(
                definition["url"],
            )
            if connected:
                status = "healthy"
            elif host_reachable:
                status = "warning"
            else:
                status = "error"
            note = probe_note
            if resolved_probe_note and resolved_probe_note != probe_note:
                note = f"{note} {resolved_probe_note}"
        elif definition.get("probe_paths"):
            status, note = probe_http_service(
                definition["url"],
                definition["probe_paths"],
            )

        docker_service = docker_index.get(definition["name"])
        container_note = None
        if docker_service:
            containers = ", ".join(docker_service.get("containers", []))
            if containers:
                container_note = (
                    f"Docker: {docker_service['status']} ({containers})"
                )
            else:
                container_note = f"Docker: {docker_service['status']}"

        entries.append({
            **definition,
            "status": status,
            "note": note,
            "container_note": container_note,
        })

    return entries


def render_service_dashboard(local_services: list[dict] | None = None) -> None:
    """Render the former HTML service dashboard directly in Streamlit."""
    st.markdown(
        '<div class="section-header"><h2>🖥️ Service Dashboard</h2></div>',
        unsafe_allow_html=True,
    )
    control_col, info_col = st.columns([1, 3])
    with control_col:
        if st.button(
            "Refresh Service Status",
            key="refresh_service_dashboard",
        ):
            st.rerun()
    with info_col:
        st.caption(
            "Live probes run against localhost endpoints and available Docker "
            "containers on each refresh."
        )

    entries = get_service_dashboard_entries(local_services)
    healthy_count = sum(1 for entry in entries if entry["status"] == "healthy")
    warning_count = sum(1 for entry in entries if entry["status"] == "warning")
    error_count = sum(1 for entry in entries if entry["status"] == "error")

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("Healthy Services", healthy_count)
    with metric_col2:
        st.metric("Warnings", warning_count)
    with metric_col3:
        st.metric("Errors", error_count)

    left_col, right_col = st.columns(2)
    for index, entry in enumerate(entries):
        target_col = left_col if index % 2 == 0 else right_col
        with target_col:
            with st.container(border=True):
                st.markdown(f"### {entry['icon']} {entry['name']}")
                st.markdown(
                    get_status_badge(entry["status"]),
                    unsafe_allow_html=True,
                )
                st.write(entry["description"])
                st.caption(entry["details"])
                if entry.get("credentials"):
                    st.caption(f"Credentials: {entry['credentials']}")
                if entry.get("container_note"):
                    st.caption(entry["container_note"])
                if entry.get("url"):
                    st.link_button(
                        entry["button"],
                        entry["url"],
                        use_container_width=True,
                    )
                else:
                    st.button(
                        entry["button"],
                        key=f"{entry['name']}_managed_button",
                        disabled=True,
                        use_container_width=True,
                    )
                st.caption(entry["note"])

    st.markdown("### 🔧 Service Status & Troubleshooting")
    st.markdown(
        "- Airbyte stability depends on the container environment variables "
        "and "
        "network wiring.\n"
        "- MLflow can appear reachable on localhost while a container is "
        "still "
        "restarting; use Docker status together with the HTTP probe.\n"
        "- KNIME workflows are managed through Airflow, so there is no "
        "separate "
        "local web console to open from this page."
    )
    st.code(
        ".\\fix_services.ps1\n"
        "docker ps --format \"table {{.Names}}\\t{{.Status}}\\t{{.Ports}}\"\n"
        "docker logs bentley-mlflow --tail 50\n"
        "docker logs bentley-airflow-webserver --tail 50",
        language="powershell",
    )


def _admin_broker_name_to_slug(name: str) -> str:
    return (name or "").strip().lower()


def _admin_get_alpaca_connector():
    from frontend.utils.secrets_helper import get_alpaca_config
    from frontend.utils.alpaca_connector import AlpacaConnector

    cfg = get_alpaca_config()
    return AlpacaConnector(
        api_key=str(cfg["api_key"]),
        secret_key=str(cfg["secret_key"]),
        paper=bool(cfg.get("paper", True)),
    )


def _admin_get_ibkr_connector():
    from frontend.utils.ibkr_connector import IBKRConnector

    gateway_url = os.getenv("IBKR_GATEWAY_URL", "https://localhost:5000")
    return IBKRConnector(gateway_url)


def _admin_get_mt5_connector(prefix: str = "MT5"):
    from frontend.utils.mt5_connector import MT5Connector

    api_url = os.getenv(f"{prefix}_API_URL") or os.getenv(
        "MT5_API_URL", "http://localhost:8002"
    )
    connector = MT5Connector(api_url)
    user = os.getenv(f"{prefix}_USER") or os.getenv("MT5_USER", "")
    password = os.getenv(f"{prefix}_PASSWORD") or os.getenv("MT5_PASSWORD", "")
    host = (
        os.getenv(f"{prefix}_HOST")
        or os.getenv(f"{prefix}_SERVER")
        or os.getenv("MT5_SERVER", "")
        or os.getenv("MT5_HOST", "")
    )
    port = int(os.getenv(f"{prefix}_PORT") or os.getenv("MT5_PORT", "443"))

    if not host or not user or not password:
        raise ValueError(
            "Missing "
            f"{prefix} credentials. Set {prefix}_USER/{prefix}_PASSWORD/"
            f"{prefix}_HOST or reuse MT5_SERVER/MT5_HOST"
        )

    if not connector.connect(user=user, password=password, host=host, port=port):
        raise RuntimeError(
            connector.last_connect_error or f"{prefix} connection failed"
        )
    return connector


def _admin_broker_action(broker_name: str, action: str) -> dict:
    slug = _admin_broker_name_to_slug(broker_name)

    try:
        if slug == "alpaca":
            connector = _admin_get_alpaca_connector()
            if action == "test":
                account = connector.get_account()
                return {
                    "ok": bool(account),
                    "message": "Alpaca authenticated" if account else (connector.last_error or "Alpaca test failed"),
                }
            if action == "refresh":
                account = connector.get_account()
                return {
                    "ok": bool(account),
                    "message": "Alpaca session refreshed" if account else (connector.last_error or "Refresh failed"),
                }
            if action == "orders":
                open_orders = connector.get_orders(status="open") or []
                return {
                    "ok": True,
                    "message": f"Loaded {len(open_orders)} open Alpaca orders",
                    "orders": open_orders[:25],
                }
            if action == "settings":
                return {
                    "ok": True,
                    "message": "Alpaca settings loaded",
                    "settings": {
                        "base_url": connector.base_url,
                        "mode": "paper" if connector.paper else "live",
                        "api_key_prefix": f"{connector.api_key[:4]}..." if connector.api_key else "",
                    },
                }

        if slug == "ibkr":
            connector = _admin_get_ibkr_connector()
            if action == "test":
                ok = connector.is_authenticated()
                return {
                    "ok": ok,
                    "message": "IBKR Gateway authenticated" if ok else "IBKR Gateway not authenticated",
                }
            if action == "refresh":
                ok = connector.reauthenticate()
                return {
                    "ok": ok,
                    "message": "IBKR reauthentication triggered" if ok else "IBKR reauthentication failed",
                }
            if action == "orders":
                orders = connector.get_live_orders() or []
                return {
                    "ok": True,
                    "message": f"Loaded {len(orders) if isinstance(orders, list) else 0} IBKR live orders",
                    "orders": orders[:25] if isinstance(orders, list) else orders,
                }
            if action == "settings":
                return {
                    "ok": True,
                    "message": "IBKR settings loaded",
                    "settings": {
                        "gateway_url": connector.base_url,
                        "websocket_url": connector.ws_url,
                        "verify_ssl": connector.verify_ssl,
                    },
                }

        if slug in {"mt5 (ftmo)", "mt5", "axi", "mt5 (axi)"}:
            prefix = "AXI_MT5" if "axi" in slug else "MT5"
            connector = _admin_get_mt5_connector(prefix=prefix)
            if action == "test":
                ok = connector.health_check()
                return {
                    "ok": ok,
                    "message": f"{prefix} bridge reachable" if ok else f"{prefix} bridge unavailable",
                }
            if action == "refresh":
                account = connector.get_account_info()
                return {
                    "ok": bool(account),
                    "message": "Account session refreshed" if account else "MT5 account refresh failed",
                }
            if action == "orders":
                positions = connector.get_positions() or []
                data = [
                    {
                        "ticket": getattr(p, "ticket", ""),
                        "symbol": getattr(p, "symbol", ""),
                        "type": getattr(p, "type", ""),
                        "volume": getattr(p, "volume", ""),
                        "profit": getattr(p, "profit", ""),
                    }
                    for p in positions
                ]
                return {
                    "ok": True,
                    "message": f"Loaded {len(data)} open MT5 positions",
                    "orders": data,
                }
            if action == "settings":
                return {
                    "ok": True,
                    "message": "MT5 settings loaded",
                    "settings": {
                        "api_url": connector.base_url,
                        "prefix": prefix,
                    },
                }

        return {
            "ok": False,
            "message": (
                f"{broker_name} is not wired in this environment yet. "
                "Supported now: Alpaca, IBKR, MT5/AXI."
            ),
        }
    except Exception as exc:
        return {
            "ok": False,
            "message": f"{broker_name} {action} failed: {exc}",
        }


def get_local_docker_services_status():
    """Return grouped Docker service status from local `docker ps` output."""
    cmd = ["docker", "ps", "--format", "{{.Names}}|{{.Status}}"]
    try:
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if result.returncode != 0:
            return None
    except Exception:
        return None

    containers = []
    for raw_line in (result.stdout or "").splitlines():
        line = raw_line.strip()
        if not line or "|" not in line:
            continue
        name, status_text = line.split("|", 1)
        containers.append({"name": name.strip(), "status_text": status_text.strip()})

    if not containers:
        return None

    def normalize_container_status(status_text: str) -> str:
        lowered = (status_text or "").lower()
        if "restarting" in lowered or "unhealthy" in lowered:
            return "warning"
        if lowered.startswith("up"):
            return "running"
        return "error"

    # Group by logical service so multiple containers (e.g., Airflow components)
    # render as a single service row.
    service_patterns = [
        ("Airflow", ["airflow"]),
        ("MLflow", ["mlflow"]),
        ("Airbyte", ["airbyte"]),
        ("MySQL", ["mysql"]),
        ("Redis", ["redis"]),
    ]

    grouped = []
    for service_name, patterns in service_patterns:
        matches = [
            c for c in containers
            if any(pattern in c["name"].lower() for pattern in patterns)
        ]
        if not matches:
            grouped.append({
                "name": service_name,
                "status": "error",
                "containers": [],
            })
            continue

        normalized = [normalize_container_status(c["status_text"]) for c in matches]
        if "error" in normalized:
            overall = "error"
        elif "warning" in normalized:
            overall = "warning"
        else:
            overall = "running"

        grouped.append({
            "name": service_name,
            "status": overall,
            "containers": [c["name"] for c in matches],
        })

    return grouped


def get_vega_ibkr_schedule_status() -> dict:
    """Return task scheduler metadata for the Vega automation task."""
    task_name = "Bentley-Vega"
    cmd = ["schtasks", "/query", "/tn", task_name, "/fo", "LIST", "/v"]
    try:
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
        if result.returncode != 0:
            return {
                "exists": False,
                "task_name": task_name,
                "error": (result.stderr or result.stdout or "Task not found").strip(),
            }

        info = {
            "exists": True,
            "task_name": task_name,
            "next_run": "Unknown",
            "last_run": "Unknown",
            "last_result": "Unknown",
            "status": "Unknown",
        }
        for line in (result.stdout or "").splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            k = key.strip().lower()
            v = value.strip()
            if k == "next run time":
                info["next_run"] = v
            elif k == "last run time":
                info["last_run"] = v
            elif k == "last result":
                info["last_result"] = v
            elif k == "status":
                info["status"] = v
        return info
    except Exception as exc:
        return {
            "exists": False,
            "task_name": task_name,
            "error": str(exc),
        }


def get_last_bot_mode_event() -> dict | None:
    """Load latest launcher event produced by start_bot_mode.ps1."""
    repo_root = Path(__file__).resolve().parents[1]
    latest_path = repo_root / "logs" / "last_bot_mode_event.json"
    if not latest_path.exists():
        return None

    try:
        with latest_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
            if isinstance(payload, dict):
                return payload
    except Exception:
        return None
    return None


@st.cache_data(ttl=15)
def get_all_bot_mode_events() -> dict:
    """Return {bot_name_lower: latest_event} by scanning bot_mode_events.jsonl.

    Falls back to last_bot_mode_event.json when the append log doesn't exist.
    """
    repo_root = Path(__file__).resolve().parents[1]
    events_path = repo_root / "logs" / "bot_mode_events.jsonl"
    per_bot: dict = {}

    if events_path.exists():
        try:
            with events_path.open("r", encoding="utf-8") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        ev = json.loads(raw)
                        if isinstance(ev, dict) and ev.get("bot"):
                            per_bot[str(ev["bot"]).lower()] = ev
                    except Exception:
                        pass
        except Exception:
            pass
    else:
        ev = get_last_bot_mode_event()
        if ev and ev.get("bot"):
            per_bot[str(ev["bot"]).lower()] = ev

    return per_bot


def build_deployed_bots_df() -> pd.DataFrame:
    """Build the Deployed Bots table by merging catalog and live launcher state."""
    catalog = get_bot_catalog_rows()
    all_events = get_all_bot_mode_events()

    rows = []
    for entry in catalog:
        bot_key = str(entry.get("bot", "")).lower()
        ev = all_events.get(bot_key, {})
        mode_raw = str(ev.get("mode", "")).lower()
        status_raw = str(ev.get("status", "")).lower()

        if mode_raw == "on" and status_raw in ("ready", "warning", "placeholder", "active"):
            status_label = "🟢 RUNNING"
        elif mode_raw == "off":
            status_label = "🔴 OFF"
        else:
            status_label = "🟡 UNKNOWN"

        rows.append(
            {
                "Bot": entry.get("bot", ""),
                "Fund": entry.get("fund", ""),
                "Strategy": entry.get("strategy", ""),
                "Status": status_label,
                "Mode": str(ev.get("trading_mode", "paper")).upper() if ev else "PAPER",
                "Broker": str(ev.get("broker", "")).upper() if ev else "",
                "Last Updated": ev.get("timestamp", "")[:19].replace("T", " ") if ev.get("timestamp") else "",
            }
        )

    return pd.DataFrame(rows)


def get_bot_launch_mode(bot_name: str, fallback_broker: str) -> str:
    if get_broker_mode_config is None:
        return "paper"

    try:
        config = get_broker_mode_config()
        broker_name = config.get_bot_broker(bot_name) or fallback_broker.lower()
        return config.get_broker_mode(broker_name)
    except Exception:
        return "paper"


def persist_bot_launch_mode(
    bot_name: str,
    trading_mode: Literal["paper", "live"],
    fallback_broker: str,
    active: bool | None = None,
) -> None:
    if get_broker_mode_config is None:
        return

    config = get_broker_mode_config()
    broker_name = config.get_bot_broker(bot_name) or fallback_broker.lower()
    config.set_broker_mode(broker_name, trading_mode)
    if active is not None:
        config.set_bot_active(bot_name, active)


def run_bot_mode(
    bot_name: str,
    mode: str,
    trading_mode: str = "paper",
    broker: str | None = None,
) -> dict:
    """Run start_bot_mode.ps1 and return execution result."""
    repo_root = Path(__file__).resolve().parents[1]
    launcher = repo_root / "start_bot_mode.ps1"

    if not launcher.exists():
        return {
            "ok": False,
            "output": f"Launcher not found: {launcher}",
        }

    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(launcher),
        "-Bot",
        bot_name,
        "-Mode",
        mode,
        "-Broker",
        broker or get_bot_default_broker(bot_name),
        "-TradingMode",
        trading_mode,
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        merged = "\n".join(
            part for part in [result.stdout.strip(), result.stderr.strip()] if part
        )
        return {
            "ok": result.returncode == 0,
            "output": merged or "No output",
        }
    except Exception as exc:
        return {"ok": False, "output": str(exc)}


# Main App
def main():
    # Check authentication first
    if not check_admin_auth():
        return
    
    # Header
    st.title("🔧 Bentley Bot Control Center")
    st.markdown(f"**Admin:** {st.session_state.admin_user} | **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Logout button in sidebar
    with st.sidebar:
        if st.button("🚪 Logout", type="secondary"):
            st.session_state.admin_authenticated = False
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 🔗 Quick Links")
        st.markdown("#### External Services")
        resolved_mlflow_url, _ = resolve_mlflow_server_url()
        st.markdown(f"[MLflow UI]({resolved_mlflow_url})")
        st.markdown("[Airflow](http://localhost:8080)")
        st.markdown("[Airbyte](http://localhost:8000)")
        st.caption("Service Dashboard is available in the Services tab.")
    
    # Navigation Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📊 Overview",
        "🖥️ Services",
        "🤖 Bot Manager",
        "🔌 Broker Health",
        "🏢 Prop Firms",
        "🛡️ Risk Engine",
        "🧠 MLflow",
        "📈 System Logs"
    ])
    local_services = get_local_docker_services_status()
    
    # TAB 1: Overview Dashboard
    with tab1:
        st.markdown('<div class="section-header"><h2>System Overview</h2></div>', unsafe_allow_html=True)
        platform_health = api_request("/platform/health", show_notice=False) or {}
        platform_architecture = api_request(
            "/platform/architecture",
            show_notice=False,
        ) or {}
        overview_services = platform_health.get("services", {})
        healthy_services = sum(
            1
            for service in overview_services.values()
            if service.get("status") == "healthy"
        )
        catalog_rows = get_bot_catalog_rows()
        
        # Health metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Configured Bots", str(len(catalog_rows)))
        with col2:
            st.metric("Healthy Services", str(healthy_services))
        with col3:
            mysql_provider = (
                platform_architecture.get("data", {})
                .get("mysql", {})
                .get("provider", "unknown")
            )
            st.metric("MySQL Provider", str(mysql_provider).upper())
        with col4:
            st.metric(
                "API Health",
                str(platform_health.get("status", "unknown")).upper(),
            )
        
        st.markdown("---")
        
        # System status
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Docker Services")
            if local_services:
                for service in local_services:
                    st.markdown(
                        get_status_badge(service["status"]) + f" **{service['name']}**",
                        unsafe_allow_html=True,
                    )
                    if service["name"] == "MySQL" and len(service["containers"]) > 1:
                        st.caption(
                            "Grouped MySQL containers: "
                            + ", ".join(service["containers"])
                        )
            else:
                services_data = api_request(
                    "/api/admin/monitoring/docker-services",
                    show_notice=False,
                )
                if services_data:
                    for service in services_data.get("services", []):
                        status_html = get_status_badge(service.get("status", "unknown"))
                        st.markdown(
                            f"{service['name']}: {status_html}",
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("Docker status unavailable. Start Docker Desktop and run containers.")
        
        with col2:
            st.subheader("Recent Activity")
            st.text("FastAPI is the unified backend entrypoint")
            st.text("Railway/local MySQL is resolved via environment-aware secrets")
            st.text("MLflow and Appwrite are exposed through platform health probes")
            st.text("Docker hosts Airflow, Airbyte, and optional MLflow services")
            st.text("Streamlit pages are Bentley UI clients over the control-center API")

        if platform_architecture:
            with st.expander("Platform Architecture Snapshot", expanded=False):
                st.json(platform_architecture)

    # TAB 2: Service Dashboard
    with tab2:
        render_service_dashboard(local_services)
    
    # TAB 3: Bot Manager
    with tab3:
        st.markdown('<div class="section-header"><h2>AI/ML Bot Orchestration</h2></div>', unsafe_allow_html=True)

        catalog_rows = get_bot_catalog_rows()
        st.caption(
            "Focus: alpha generation via price forecasting and portfolio optimization, "
            "including simulated rebalancing guidance and execution-aware deployment."
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Mansa Funds", str(len(catalog_rows)))
        with c2:
            st.metric("Configured Bots", str(len(catalog_rows)))
        with c3:
            st.metric("Orchestration Scope", "Forecast + Rebalance")

        st.markdown("**Mansa Capital Fund/Bot Strategy Catalog**")
        catalog_df = pd.DataFrame(catalog_rows).rename(columns={
            "bot": "Bot Name",
            "fund": "Mansa Fund",
            "strategy": "Proposed Strategy",
        })
        st.dataframe(catalog_df, use_container_width=True, hide_index=True)
        st.markdown("---")

        st.subheader("Vega Automation")
        schedule = get_vega_ibkr_schedule_status()
        last_event = get_last_bot_mode_event()
        vega_launch_mode = st.radio(
            "Vega trading mode",
            options=["paper", "live"],
            horizontal=True,
            key="vega_trading_mode",
            index=0 if get_bot_launch_mode("Vega", "ibkr") == "paper" else 1,
        )

        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("Task", "Configured" if schedule.get("exists") else "Missing")
        with col_b:
            st.metric("Next Run", schedule.get("next_run", "Unknown"))
        with col_c:
            st.metric("Last Result", schedule.get("last_result", "Unknown"))
        with col_d:
            event_status = (last_event or {}).get("status", "n/a")
            st.metric("Last Vega Status", str(event_status))

        st.caption(f"Selected Vega mode: {vega_launch_mode.upper()}")

        btn_on, btn_off = st.columns(2)
        with btn_on:
            if st.button("Vega ON", type="primary", use_container_width=True):
                persist_bot_launch_mode("Vega", vega_launch_mode, "ibkr", True)
                with st.spinner("Running Vega ON..."):
                    execution = run_bot_mode(
                        "Vega",
                        "ON",
                        vega_launch_mode,
                        broker="IBKR",
                    )
                st.session_state["vega_mode_output"] = execution["output"]
                if execution["ok"]:
                    st.success("Vega ON completed.")
                else:
                    st.error("Vega ON failed.")
                st.rerun()
        with btn_off:
            if st.button("Vega OFF", use_container_width=True):
                persist_bot_launch_mode("Vega", vega_launch_mode, "ibkr", False)
                with st.spinner("Running Vega OFF..."):
                    execution = run_bot_mode(
                        "Vega",
                        "OFF",
                        vega_launch_mode,
                        broker="IBKR",
                    )
                st.session_state["vega_mode_output"] = execution["output"]
                if execution["ok"]:
                    st.success("Vega OFF completed.")
                else:
                    st.error("Vega OFF failed.")
                st.rerun()

        if schedule.get("exists"):
            st.caption(
                f"Task {schedule.get('task_name')} status: {schedule.get('status', 'Unknown')}"
            )
        else:
            st.warning(
                "Vega task is not configured yet. "
                "Run setup from terminal to register Bentley-Vega."
            )

        if last_event:
            st.caption("Latest launcher event (from logs/last_bot_mode_event.json)")
            st.json(last_event)

        vega_output = st.session_state.get("vega_mode_output")
        if vega_output:
            with st.expander("Last Vega Command Output", expanded=False):
                st.code(vega_output, language="text")

        st.markdown("---")
        st.subheader("Hydra Operations")
        hydra_snapshot = get_hydra_control_snapshot()
        hydra_status = hydra_snapshot.get("status") or {}
        hydra_health = hydra_snapshot.get("health") or {}
        hydra_launch_mode = st.radio(
            "Hydra trading mode",
            options=["paper", "live"],
            horizontal=True,
            key="hydra_trading_mode",
            index=(
                0 if get_bot_launch_mode("Hydra", "alpaca") == "paper" else 1
            ),
        )

        h1, h2, h3, h4 = st.columns(4)
        with h1:
            st.metric(
                "Hydra Execution",
                "ON" if hydra_status.get("execution_enabled") else "OFF",
            )
        with h2:
            st.metric(
                "Latest Hydra Action",
                str(hydra_status.get("last_analysis", {}).get("action", "N/A")),
            )
        with h3:
            st.metric(
                "Hydra FastAPI",
                str(
                    hydra_health.get("fastapi", {}).get("reachable", False)
                ).upper(),
            )
        with h4:
            st.metric(
                "Hydra Airbyte",
                str(
                    hydra_health.get("airbyte", {}).get("reachable", False)
                ).upper(),
            )

        hydra_btn1, hydra_btn2, hydra_btn3 = st.columns(3)
        with hydra_btn1:
            if st.button("Hydra ON", type="primary", use_container_width=True):
                persist_bot_launch_mode("Hydra", hydra_launch_mode, "alpaca", True)
                with st.spinner("Running Hydra ON..."):
                    execution = run_bot_mode(
                        "Hydra",
                        "ON",
                        hydra_launch_mode,
                        broker="ALPACA",
                    )
                st.session_state["hydra_mode_output"] = execution["output"]
                if execution["ok"]:
                    st.success("Hydra ON completed.")
                else:
                    st.error("Hydra ON failed.")
                st.rerun()
        with hydra_btn2:
            if st.button("Hydra OFF", use_container_width=True):
                persist_bot_launch_mode("Hydra", hydra_launch_mode, "alpaca", False)
                with st.spinner("Running Hydra OFF..."):
                    execution = run_bot_mode(
                        "Hydra",
                        "OFF",
                        hydra_launch_mode,
                        broker="ALPACA",
                    )
                st.session_state["hydra_mode_output"] = execution["output"]
                if execution["ok"]:
                    st.success("Hydra OFF completed.")
                else:
                    st.error("Hydra OFF failed.")
                st.rerun()
        with hydra_btn3:
            if st.button("Bootstrap Hydra", use_container_width=True):
                result = api_request(
                    "/hydra/bootstrap",
                    method="POST",
                    show_notice=True,
                )
                if result:
                    st.success("Hydra bootstrap completed.")
                    st.session_state["hydra_bootstrap_result"] = result
                else:
                    st.error("Hydra bootstrap failed.")

        hydra_bootstrap_result = st.session_state.get("hydra_bootstrap_result")
        if hydra_bootstrap_result:
            with st.expander("Hydra Bootstrap Result", expanded=False):
                st.json(hydra_bootstrap_result)

        hydra_output = st.session_state.get("hydra_mode_output")
        if hydra_output:
            with st.expander("Last Hydra Command Output", expanded=False):
                st.code(hydra_output, language="text")

        with st.expander("Hydra Health Details", expanded=False):
            st.json(hydra_snapshot)

        st.markdown("---")
        st.subheader("Triton Operations")
        triton_snapshot = get_triton_control_snapshot()
        triton_status = triton_snapshot.get("status") or {}
        triton_health = triton_snapshot.get("health") or {}
        triton_launch_mode = st.radio(
            "Triton trading mode",
            options=["paper", "live"],
            horizontal=True,
            key="triton_trading_mode",
            index=(
                0 if get_bot_launch_mode("Triton", "alpaca") == "paper" else 1
            ),
        )

        t1, t2, t3, t4 = st.columns(4)
        with t1:
            st.metric(
                "Triton Execution",
                "ON" if triton_status.get("execution_enabled") else "OFF",
            )
        with t2:
            st.metric(
                "Latest Triton Action",
                str(triton_status.get("last_analysis", {}).get("action", "N/A")),
            )
        with t3:
            st.metric(
                "Triton FastAPI",
                str(
                    triton_health.get("fastapi", {}).get("reachable", False)
                ).upper(),
            )
        with t4:
            st.metric(
                "Triton MLflow",
                str(
                    triton_health.get("mlflow", {}).get("reachable", False)
                ).upper(),
            )

        triton_btn1, triton_btn2, triton_btn3 = st.columns(3)
        with triton_btn1:
            if st.button("Triton ON", type="primary", use_container_width=True):
                persist_bot_launch_mode(
                    "Triton",
                    triton_launch_mode,
                    "alpaca",
                    True,
                )
                with st.spinner("Running Triton ON..."):
                    execution = run_bot_mode(
                        "Triton",
                        "ON",
                        triton_launch_mode,
                        broker="ALPACA",
                    )
                st.session_state["triton_mode_output"] = execution["output"]
                if execution["ok"]:
                    st.success("Triton ON completed.")
                else:
                    st.error("Triton ON failed.")
                st.rerun()

        with triton_btn2:
            if st.button("Triton OFF", use_container_width=True):
                persist_bot_launch_mode(
                    "Triton",
                    triton_launch_mode,
                    "alpaca",
                    False,
                )
                with st.spinner("Running Triton OFF..."):
                    execution = run_bot_mode(
                        "Triton",
                        "OFF",
                        triton_launch_mode,
                        broker="ALPACA",
                    )
                st.session_state["triton_mode_output"] = execution["output"]
                if execution["ok"]:
                    st.success("Triton OFF completed.")
                else:
                    st.error("Triton OFF failed.")
                st.rerun()

        with triton_btn3:
            if st.button("Bootstrap Triton", use_container_width=True):
                result = api_request(
                    "/triton/bootstrap",
                    method="POST",
                    show_notice=True,
                )
                if result:
                    st.success("Triton bootstrap completed.")
                    st.session_state["triton_bootstrap_result"] = result
                else:
                    st.error("Triton bootstrap failed.")

        triton_trade_col1, triton_trade_col2, triton_trade_col3, triton_trade_col4 = st.columns(
            4
        )
        with triton_trade_col1:
            triton_trade_ticker = st.text_input(
                "Triton ticker",
                value="IYT",
                key="triton_trade_ticker",
            ).strip().upper()
        with triton_trade_col2:
            triton_trade_action = st.selectbox(
                "Triton action",
                ["BUY", "SELL"],
                key="triton_trade_action",
            )
        with triton_trade_col3:
            triton_trade_qty = st.number_input(
                "Triton quantity",
                min_value=1.0,
                value=5.0,
                step=1.0,
                key="triton_trade_qty",
            )
        with triton_trade_col4:
            triton_trade_dry_run = st.toggle(
                "Dry Run",
                value=True,
                key="triton_trade_dry_run",
            )

        if st.button("Execute Triton Trade", use_container_width=True):
            trade_result = api_request(
                "/triton/trade",
                method="POST",
                data={
                    "broker": "alpaca",
                    "ticker": triton_trade_ticker or "IYT",
                    "action": triton_trade_action,
                    "qty": float(triton_trade_qty),
                    "dry_run": bool(triton_trade_dry_run),
                },
                show_notice=True,
            )
            if trade_result:
                st.success("Triton trade request completed.")
                st.session_state["triton_trade_result"] = trade_result
            else:
                st.error("Triton trade request failed.")

        triton_bootstrap_result = st.session_state.get("triton_bootstrap_result")
        if triton_bootstrap_result:
            with st.expander("Triton Bootstrap Result", expanded=False):
                st.json(triton_bootstrap_result)

        triton_trade_result = st.session_state.get("triton_trade_result")
        if triton_trade_result:
            with st.expander("Last Triton Trade Result", expanded=False):
                st.json(triton_trade_result)

        triton_output = st.session_state.get("triton_mode_output")
        if triton_output:
            with st.expander("Last Triton Command Output", expanded=False):
                st.code(triton_output, language="text")

        with st.expander("Triton Health Details", expanded=False):
            st.json(triton_snapshot)

        st.markdown("---")

        # Bot deployment controls
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader("Deployed Bots")
        with col2:
            if st.button("➕ Deploy New Bot", type="primary"):
                st.session_state.show_deploy_modal = True

        # ── Live launcher status (always shown) ──────────────────────────
        deployed_df = build_deployed_bots_df()
        st.dataframe(deployed_df, use_container_width=True, hide_index=True)

        col_run, col_cnt = st.columns(2)
        n_running = len(deployed_df[deployed_df["Status"].str.startswith("🟢")])
        n_off = len(deployed_df[deployed_df["Status"].str.startswith("🔴")])
        col_run.metric("🟢 Running", n_running)
        col_cnt.metric("🔴 Off", n_off)

        # ── API-sourced data overlay (if available) ───────────────────────
        bots_data = api_request("/api/admin/bots/list")
        if bots_data:
            bots_df = pd.DataFrame(bots_data.get("bots", []))
            if not bots_df.empty:
                if "bot_name" not in bots_df.columns and "name" in bots_df.columns:
                    bots_df["bot_name"] = bots_df["name"]
                if "mansa_fund" not in bots_df.columns:
                    bots_df["mansa_fund"] = "Mansa Fund"

                fund_to_bot = {
                    "mansa minerals - gold strategy": "Orion",
                    "mansa_minerals": "Orion",
                    "mansa minerals": "Orion",
                }

                def normalize_bot_name(row):
                    fund_value = str(row.get("mansa_fund", "")).strip().lower()
                    if fund_value in fund_to_bot:
                        return fund_to_bot[fund_value]
                    return row.get("bot_name", "")

                bots_df["bot_name"] = bots_df.apply(normalize_bot_name, axis=1)

                display_cols = ["bot_name", "mansa_fund", "status", "broker", "uptime"]
                available_cols = [col for col in display_cols if col in bots_df.columns]
                display_df = bots_df[available_cols].copy()
                display_df = display_df.rename(columns={
                    "bot_name": "Bot Name",
                    "mansa_fund": "Mansa Fund",
                    "status": "Status",
                    "broker": "Broker",
                    "uptime": "Uptime",
                })
                with st.expander("API Bot List (supplemental)", expanded=False):
                    st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Deploy modal
        if st.session_state.get("show_deploy_modal", False):
            with st.expander("Deploy New Bot", expanded=True):
                _catalog = get_bot_catalog_rows()
                bot_select = st.selectbox("Select Bot", [row["bot"] for row in _catalog])
                broker_select = st.selectbox("Select Broker", ["Alpaca", "IBKR", "Binance", "MT5 (FTMO)", "MT5 (Axi)"])
                environment = st.radio("Environment", ["Sandbox", "Live"], horizontal=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Deploy", type="primary", use_container_width=True):
                        st.success(f"Deploying {bot_select} to {broker_select} ({environment})...")
                        st.session_state.show_deploy_modal = False
                        st.rerun()
                with col2:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state.show_deploy_modal = False
                        st.rerun()
    
    # TAB 4: Broker Health
    with tab4:
        st.markdown('<div class="section-header"><h2>Multi-Broker Orchestration</h2></div>', unsafe_allow_html=True)
        
        # Refresh button
        if st.button("🔄 Refresh All Sessions"):
            st.info("Refreshing broker sessions...")
        
        st.markdown("---")
        
        # Broker status cards
        brokers_data = api_request("/api/admin/brokers/health")
        
        if not brokers_data:
            # Sample broker data
            brokers = [
                {"name": "Alpaca", "status": "healthy", "latency": "45ms", "orders_today": 12, "last_sync": "2 min ago"},
                {"name": "Schwab", "status": "warning", "latency": "120ms", "orders_today": 0, "last_sync": "15 min ago"},
                {"name": "IBKR", "status": "error", "latency": "N/A", "orders_today": 0, "last_sync": "Never"},
                {"name": "Binance", "status": "healthy", "latency": "35ms", "orders_today": 8, "last_sync": "1 min ago"},
                {"name": "Coinbase", "status": "idle", "latency": "N/A", "orders_today": 0, "last_sync": "Never"},
            ]
        else:
            brokers = brokers_data.get("brokers", [])
        
        for broker in brokers:
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
            
            with col1:
                st.markdown(f"### {broker['name']}")
            with col2:
                st.markdown(get_status_badge(broker['status']), unsafe_allow_html=True)
            with col3:
                st.metric("Latency", broker['latency'])
            with col4:
                st.metric("Orders Today", broker['orders_today'])
            with col5:
                st.text(f"Last sync: {broker['last_sync']}")
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("Test Connection", key=f"{broker['name']}_test"):
                    result = _admin_broker_action(broker['name'], "test")
                    if result.get("ok"):
                        st.success(result.get("message", "Connection test passed"))
                    else:
                        st.error(result.get("message", "Connection test failed"))
            with col2:
                if st.button("Refresh Token", key=f"{broker['name']}_refresh"):
                    result = _admin_broker_action(broker['name'], "refresh")
                    if result.get("ok"):
                        st.success(result.get("message", "Refresh completed"))
                    else:
                        st.error(result.get("message", "Refresh failed"))
            with col3:
                if st.button("View Orders", key=f"{broker['name']}_orders"):
                    result = _admin_broker_action(broker['name'], "orders")
                    if result.get("ok"):
                        st.success(result.get("message", "Orders loaded"))
                        orders_payload = result.get("orders")
                        if isinstance(orders_payload, list) and orders_payload:
                            st.dataframe(pd.DataFrame(orders_payload), use_container_width=True, hide_index=True)
                        elif orders_payload:
                            st.json(orders_payload)
                        else:
                            st.info("No orders available")
                    else:
                        st.error(result.get("message", "Order load failed"))
            with col4:
                if st.button("Settings", key=f"{broker['name']}_settings"):
                    result = _admin_broker_action(broker['name'], "settings")
                    if result.get("ok"):
                        st.success(result.get("message", "Settings loaded"))
                        settings_payload = result.get("settings")
                        if settings_payload:
                            st.json(settings_payload)
                    else:
                        st.error(result.get("message", "Settings unavailable"))
            
            st.markdown("---")
    
    # TAB 5: Prop Firms
    with tab5:
        st.markdown('<div class="section-header"><h2>Prop Firm Execution Management</h2></div>', unsafe_allow_html=True)
        
        # Prop firm status
        prop_firms = [
            {"name": "FTMO", "platform": "MT5", "accounts": 2, "status": "active", "daily_pnl": "$234.56"},
            {"name": "Axi Select", "platform": "MT5", "accounts": 1, "status": "active", "daily_pnl": "$89.12"},
            {"name": "Zenit", "platform": "NinjaTrader", "accounts": 0, "status": "planned", "daily_pnl": "$0.00"},
        ]
        
        for firm in prop_firms:
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
            
            with col1:
                st.markdown(f"### {firm['name']}")
            with col2:
                st.text(f"Platform: {firm['platform']}")
            with col3:
                st.metric("Active Accounts", firm['accounts'])
            with col4:
                st.markdown(get_status_badge(firm['status']), unsafe_allow_html=True)
            with col5:
                st.metric("Daily P&L", firm['daily_pnl'])
            
            # MT5 controls
            if firm['platform'] == "MT5" and firm['accounts'] > 0:
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"View Positions", key=f"{firm['name']}_positions"):
                        st.info(f"Loading {firm['name']} positions...")
                with col2:
                    if st.button(f"Challenge Status", key=f"{firm['name']}_challenge"):
                        st.info(f"Loading {firm['name']} challenge metrics...")
                with col3:
                    if st.button(f"Execute Trade", key=f"{firm['name']}_trade"):
                        st.info(f"Opening trade form for {firm['name']}...")
            
            st.markdown("---")
    
    # TAB 6: Risk Engine
    with tab6:
        st.markdown('<div class="section-header"><h2>Risk Management & Compliance</h2></div>', unsafe_allow_html=True)
        st.caption(
            "Portfolio optimization lens: monitor liquidity, drawdown, and concentration "
            "to inform fund-level repositioning and rebalance cadence."
        )
        
        # Risk metrics (Row 1)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Portfolio Drawdown", "-2.3%", "Within limits")
        with col2:
            st.metric("Margin Utilization", "34%", "Healthy")
        with col3:
            st.metric("Risk Violations Today", "0", "✓")
        with col4:
            # NEW: Trade Liquidity Ratio
            liquidity_ratio = 26.5  # Example: 26.5% cash available
            ratio_delta = "+3.2%" if liquidity_ratio >= 20 else "-Warning"
            ratio_color = "normal" if liquidity_ratio >= 20 else "inverse"
            st.metric("Trade Liquidity Ratio", f"{liquidity_ratio}%", ratio_delta, delta_color=ratio_color)
        
        st.markdown("---")
        
        # NEW: Liquidity Management Section
        st.markdown('<div class="section-header"><h3>💧 Liquidity & Dry Powder Management</h3></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**Automatic Trade Liquidity Settings**")
            st.caption("Ensure sufficient cash reserves for alternative opportunities and market mobility")
            
            # Cash Reserve Buffer
            liquidity_buffer = st.slider(
                "Cash Reserve Buffer (%)", 
                min_value=10, 
                max_value=50, 
                value=25, 
                step=5,
                help="Recommended: 20-30% for optimal liquidity and opportunity capture"
            )
            
            # Profit Benchmark
            profit_benchmark = st.number_input(
                "Profit Benchmark for Liquidity Release (%)", 
                min_value=0.0, 
                max_value=100.0, 
                value=15.0, 
                step=0.5,
                help="When trades reach this profit %, release funds back to liquidity pool"
            )
            
            # Auto-rebalance
            auto_rebalance = st.checkbox(
                "Auto-rebalance to maintain liquidity buffer", 
                value=True,
                help="Automatically adjust positions to maintain target cash reserve"
            )
        
        with col2:
            st.markdown("**💰 Available Dry Powder**")
            
            # Sample calculations (replace with actual portfolio data)
            total_portfolio_value = 100000  # Example
            current_cash = total_portfolio_value * (liquidity_ratio / 100)
            target_cash = total_portfolio_value * (liquidity_buffer / 100)
            available_for_trades = max(0, current_cash - target_cash)
            
            st.metric("Total Cash", f"${current_cash:,.0f}")
            st.metric("Reserved Buffer", f"${target_cash:,.0f}")
            st.metric("Available Now", f"${available_for_trades:,.0f}", 
                     "Ready for deployment" if available_for_trades > 0 else "At limit")
            
            # Liquidity health indicator
            if liquidity_ratio >= liquidity_buffer:
                st.success("✅ Healthy liquidity position")
            elif liquidity_ratio >= (liquidity_buffer - 5):
                st.warning("⚠️ Approaching liquidity minimum")
            else:
                st.error("🔴 Below liquidity buffer")
        
        st.markdown("---")
        
        # Risk settings
        st.subheader("Risk Limits Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            max_drawdown = st.slider("Max Portfolio Drawdown (%)", 0, 20, 5)
            max_position_size = st.slider("Max Position Size (%)", 0, 50, 10)
            max_leverage = st.slider("Max Leverage", 1, 10, 3)
        
        with col2:
            daily_loss_limit = st.number_input("Daily Loss Limit ($)", value=1000)
            concentration_limit = st.number_input("Single Asset Concentration (%)", value=25)
            
            st.checkbox("Enable pre-trade risk checks", value=True)
            st.checkbox("Enable real-time monitoring", value=True)
            st.checkbox("Auto-halt on violation", value=True)
        
        if st.button("💾 Save Risk Settings", type="primary"):
            st.success("Risk settings updated successfully!")
            st.info(f"Liquidity buffer set to {liquidity_buffer}% | Profit benchmark at {profit_benchmark}%")
        
        st.markdown("---")
        
        # Liquidity deployment strategy
        with st.expander("📊 Liquidity Deployment Strategy"):
            st.markdown("""
            **How the Trade Liquidity Ratio works:**
            
            1. **Cash Reserve Buffer**: Maintains {buffer}% cash for rapid deployment on opportunities
            2. **Profit Benchmark**: When positions hit {benchmark}% profit, reallocate to liquidity pool
            3. **Auto-Rebalance**: System automatically adjusts to maintain target liquidity
            4. **Dry Powder Calculation**: `Available = Current Cash - Reserved Buffer`
            
            **Example:**
            - Portfolio Value: $100,000
            - Target Buffer: 25% → $25,000 reserved
            - Current Cash: 26.5% → $26,500
            - **Available Dry Powder: $1,500** for new opportunities
            
            This ensures you always have capital ready for:
            - Alternative trading opportunities
            - Market volatility response
            - Quick position adjustments
            - Opportunistic entries
            """.format(buffer=liquidity_buffer, benchmark=profit_benchmark))
        
        st.markdown("---")
        
        # Recent violations
        st.subheader("Recent Risk Events")
        st.text("No violations in the last 24 hours ✓")
    
    # TAB 7: MLflow Integration
    with tab7:
        st.markdown('<div class="section-header"><h2>🧠 MLflow Experiment Tracking</h2></div>', unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("🔌 MLflow Server Status")
            configured_mlflow_url = DEFAULT_MLFLOW_URL
            resolved_mlflow_url, resolved_probe_note = resolve_mlflow_server_url()
            mlflow_scheme = urlparse(configured_mlflow_url).scheme.lower()
            if mlflow_scheme not in ("http", "https"):
                st.warning(
                    "⚠️ MLflow UI URL must be HTTP/HTTPS. "
                    f"Current value: {configured_mlflow_url}"
                )
                st.info(
                    "Set `MLFLOW_SERVER_URL` to your tracking server URL, "
                    "e.g. `http://localhost:5000`"
                )
            else:
                connected, host_reachable, probe_note = probe_mlflow_server(
                    resolved_mlflow_url
                )
                if connected:
                    if resolved_mlflow_url != configured_mlflow_url:
                        st.success(
                            "✅ MLflow server reachable at "
                            f"{resolved_mlflow_url} "
                            f"(resolved from {configured_mlflow_url})"
                        )
                    else:
                        st.success(
                            f"✅ MLflow server reachable at {resolved_mlflow_url}"
                        )
                    st.caption(probe_note or resolved_probe_note)
                elif host_reachable:
                    st.warning(
                        "⚠️ Host is reachable at "
                        f"{resolved_mlflow_url}, but MLflow endpoints "
                        "were not detected."
                    )
                    st.info(
                        "Verify `MLFLOW_SERVER_URL` points to the MLflow "
                        "server and not another service."
                    )
                else:
                    st.error(
                        f"❌ Cannot connect to MLflow server at {configured_mlflow_url}"
                    )
                    backend_store_uri = get_mlflow_backend_store_uri()
                    st.info(
                        "Start MLflow: "
                        f"`python -m mlflow server --backend-store-uri "
                        f"\"{backend_store_uri}\" --host 0.0.0.0 --port 5000`"
                    )

        with col2:
            st.subheader("🔗 Quick Actions")
            if st.button("🔄 Refresh MLflow Data", type="primary", use_container_width=True):
                st.session_state.pop("resolved_mlflow_server_url", None)
                st.session_state.pop("resolved_mlflow_server_note", None)
                st.rerun()
            if st.button("🌐 Open MLflow UI", use_container_width=True):
                st.markdown(f"[Open MLflow UI]({resolved_mlflow_url})")

        st.markdown("---")
        st.subheader("📋 Recent Experiments")

        try:
            import mlflow
            from mlflow.tracking import MlflowClient

            resolved_tracking_uri = get_resolved_mlflow_tracking_uri()
            mlflow.set_tracking_uri(resolved_tracking_uri)
            client = MlflowClient(tracking_uri=resolved_tracking_uri)
            experiments = client.search_experiments()

            exp_rows = []
            total_runs = 0
            finished_runs = 0
            run_frames = []

            for exp in experiments[:25]:
                runs = mlflow.search_runs(
                    experiment_ids=[exp.experiment_id],
                    max_results=200,
                )
                run_count = len(runs)
                total_runs += run_count
                if not runs.empty and "status" in runs.columns:
                    finished_runs += len(runs[runs["status"] == "FINISHED"])
                    annotated = runs.copy()
                    annotated["experiment_name"] = exp.name
                    annotated["experiment_id"] = exp.experiment_id
                    run_frames.append(annotated)

                last_updated = "N/A"
                if not runs.empty and "start_time" in runs.columns:
                    ts = pd.to_datetime(runs["start_time"]).max()
                    if pd.notna(ts):
                        last_updated = ts.strftime('%Y-%m-%d %H:%M:%S')

                exp_rows.append({
                    "Experiment": exp.name,
                    "Experiment ID": exp.experiment_id,
                    "Lifecycle Stage": exp.lifecycle_stage,
                    "Runs": run_count,
                    "Last Updated": last_updated,
                })

            success_rate = (finished_runs / total_runs * 100) if total_runs > 0 else 0.0

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Active Experiments", len(experiments), "")
            with m2:
                st.metric("Total Runs", total_runs, "")
            with m3:
                st.metric("Finished Runs", finished_runs, "")
            with m4:
                st.metric("Success Rate", f"{success_rate:.1f}%", "")

            if exp_rows:
                st.dataframe(pd.DataFrame(exp_rows), use_container_width=True, hide_index=True)
            else:
                st.info("No experiments found.")

            all_runs_df = (
                pd.concat(run_frames, ignore_index=True)
                if run_frames
                else pd.DataFrame()
            )

            st.markdown("---")
            st.subheader("🧭 Titan MLflow Blueprint")
            st.caption(
                "Titan runs now carry feature-level discipline context, "
                "registry lineage, and benchmark metadata for Orion, Rigel, and Dogon comparisons."
            )
            st.dataframe(
                pd.DataFrame(TITAN_MLFLOW_SCHEMA_ROWS),
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("---")
            st.subheader("🗂️ Model Registry")
            registry_df = build_model_registry_frame(client)
            if not registry_df.empty:
                st.dataframe(
                    registry_df,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No registered models found in MLflow registry.")

            st.markdown("---")
            st.subheader("⚖️ Cross-Bot Benchmarking")
            benchmark_df = build_mlflow_benchmark_frame(all_runs_df)
            if not benchmark_df.empty:
                st.dataframe(
                    benchmark_df,
                    use_container_width=True,
                    hide_index=True,
                )
                missing_bots = benchmark_df[benchmark_df["Runs"] == 0]["Bot"].tolist()
                if missing_bots:
                    st.info(
                        "MLflow has no benchmark runs yet for: "
                        + ", ".join(missing_bots)
                    )
            else:
                st.info("No MLflow run data available for Titan/Orion/Rigel/Dogon benchmarking.")

            st.markdown("---")
            st.subheader("🧪 Titan Forensic Runs")
            titan_forensic_df = build_titan_forensic_frame(all_runs_df)
            if not titan_forensic_df.empty:
                st.dataframe(
                    titan_forensic_df,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info(
                    "No Titan run metrics with forensic feature snapshots were found yet. "
                    "Run Titan once with the updated logging to populate this view."
                )

        except Exception as e:
            error_text = str(e)
            st.error(f"❌ Failed to load experiments: {error_text}")
            if "Can't locate revision identified by" in error_text:
                st.warning("⚠️ MLflow database migrations are out of sync.")
                st.code(f"mlflow db upgrade \"{get_mlflow_backend_store_uri()}\"", language="bash")
            else:
                st.info("Make sure MLflow server is running and tracking URI points to the server URL.")

        st.markdown("---")
        with st.expander("⚙️ MLflow Configuration"):
            resolved_mlflow_url, _ = resolve_mlflow_server_url()
            resolved_tracking_uri = get_resolved_mlflow_tracking_uri()
            st.code(f"""
# MLflow Configuration
CONFIGURED_TRACKING_URI: {DEFAULT_MLFLOW_TRACKING_URI}
RESOLVED_TRACKING_URI: {resolved_tracking_uri}
CONFIGURED_SERVER_URL: {DEFAULT_MLFLOW_URL}
RESOLVED_SERVER_URL: {resolved_mlflow_url}
BACKEND_STORE_URI: {get_mlflow_backend_store_uri()}

# Notes
- MLflow Training dashboard is merged into this ACC tab.
- Use SERVER_URL for web health checks/UI.
- Use BACKEND_STORE_URI for `mlflow db upgrade`.
            """, language="text")
    
    # TAB 8: System Logs
    with tab8:
        st.markdown('<div class="section-header"><h2>Execution Logs & Monitoring</h2></div>', unsafe_allow_html=True)
        
        # Log filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            log_level = st.selectbox("Log Level", ["All", "INFO", "WARNING", "ERROR"])
        with col2:
            log_source = st.selectbox("Source", ["All", "Bots", "Brokers", "Prop Firms", "Risk"])
        with col3:
            time_range = st.selectbox("Time Range", ["Last Hour", "Last 24h", "Last 7 days"])
        
        # Log display
        st.text_area("System Logs", value="""
[2026-02-15 15:23:45] [INFO] [Bot3] Successfully deployed to Alpaca (sandbox)
[2026-02-15 14:45:12] [INFO] [Alpaca] Session token refreshed successfully
[2026-02-15 13:12:34] [INFO] [FTMO-MT5] Trade executed: EURUSD BUY 0.1 lots @ 1.0945
[2026-02-15 11:30:22] [WARNING] [Schwab] High latency detected: 180ms
[2026-02-15 09:15:11] [INFO] [System] Daily reconciliation completed successfully
[2026-02-15 08:00:05] [INFO] [Risk] All systems within risk parameters
        """, height=400)
        
        # Export logs
        if st.button("📥 Export Logs"):
            st.info("Exporting logs to CSV...")


# Run the app
if __name__ == "__main__":
    main()


