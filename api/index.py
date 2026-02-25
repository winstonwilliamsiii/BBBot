"""
Vercel Serverless API Handler for BentleyBudgetBot
Adds CORS and simple API key auth for /api/* endpoints.
"""

import json
import os
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import requests


ALLOWED_ORIGIN = os.getenv("FRONTEND_ORIGIN", "https://bbbot305.streamlit.app")
API_KEY = os.getenv("API_GATEWAY_KEY")
TRADINGVIEW_WEBHOOK_SECRET = os.getenv("TRADINGVIEW_WEBHOOK_SECRET")
VEGA_BOT_WEBHOOK_URL = os.getenv("VEGA_BOT_WEBHOOK_URL")
DISCORD_WEBHOOK = (
    os.getenv("DISCORD_WEBHOOK")
    or os.getenv("DISCORD_WEBHOOK_PROD")
)
VEGA_PAPER_ONLY = os.getenv("VEGA_PAPER_ONLY", "true").strip().lower()
VEGA_LIVE_MODE_KEY = os.getenv("VEGA_LIVE_MODE_KEY")


def _is_truthy(value):
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _request_headers(request):
    raw_headers = getattr(request, "headers", {}) or {}

    headers = {}
    if isinstance(raw_headers, dict):
        for key, value in raw_headers.items():
            headers[str(key).lower()] = value
    return headers


def _request_query_params(request, path: str):
    params = {}
    query = getattr(request, "query", None)
    if isinstance(query, dict):
        for key, value in query.items():
            if isinstance(value, list):
                params[str(key)] = value[0] if value else None
            else:
                params[str(key)] = value

    if "?" in path:
        try:
            parsed = parse_qs(urlparse(path).query)
            for key, values in parsed.items():
                if key not in params:
                    params[key] = values[0] if values else None
        except ValueError:
            pass

    return params


def _request_json_body(request):
    payload = None
    raw_text = ""

    get_json = getattr(request, "get_json", None)
    if callable(get_json):
        try:
            payload = get_json()
        except (TypeError, ValueError, json.JSONDecodeError):
            payload = None

    if payload is None:
        payload = getattr(request, "json", None)

    if payload is None:
        body = getattr(request, "body", None)
        if body is None:
            body = getattr(request, "data", None)

        if isinstance(body, bytes):
            raw_text = body.decode("utf-8", errors="ignore").strip()
        elif isinstance(body, str):
            raw_text = body.strip()
        elif isinstance(body, (dict, list)):
            payload = body

    if payload is None and raw_text:
        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            payload = {"message": raw_text}

    if payload is None:
        payload = {}

    return payload, raw_text


def _redact_payload(payload: dict):
    if not isinstance(payload, dict):
        return payload

    redacted = {}
    sensitive_keys = {"secret", "passphrase", "token", "api_key", "x_api_key"}
    for key, value in payload.items():
        if str(key).lower() in sensitive_keys:
            redacted[key] = "***"
        else:
            redacted[key] = value
    return redacted


def _normalize_tradingview_payload(payload: dict):
    if not isinstance(payload, dict):
        return {}

    symbol = payload.get("symbol") or payload.get("ticker")
    side = (
        payload.get("action")
        or payload.get("side")
        or payload.get("strategy.order.action")
    )
    timeframe = payload.get("timeframe") or payload.get("interval")

    return {
        "symbol": symbol,
        "side": side,
        "timeframe": timeframe,
        "strategy": payload.get("strategy") or payload.get("strategy_name"),
        "price": payload.get("price") or payload.get("close"),
        "alert_name": payload.get("alert_name") or payload.get("name"),
    }


def _send_discord_alert(normalized: dict):
    if not DISCORD_WEBHOOK:
        return {"sent": False, "reason": "DISCORD_WEBHOOK not configured"}

    symbol = normalized.get("symbol") or "UNKNOWN"
    side = normalized.get("side") or "signal"
    timeframe = normalized.get("timeframe") or "n/a"
    strategy = normalized.get("strategy") or "Vega Mansa Retail"
    price = normalized.get("price")

    content = (
        f"📡 TradingView Alert | {strategy} | {symbol} | "
        f"{side} | TF: {timeframe}"
    )
    if price is not None:
        content += f" | Price: {price}"

    body = {
        "content": content,
        "embeds": [
            {
                "title": "TradingView Screener Alert",
                "description": "Webhook received by Bentley Vega endpoint",
                "fields": [
                    {"name": "Symbol", "value": str(symbol), "inline": True},
                    {"name": "Side", "value": str(side), "inline": True},
                    {
                        "name": "Timeframe",
                        "value": str(timeframe),
                        "inline": True,
                    },
                ],
                "timestamp": datetime.now().isoformat(),
            }
        ],
    }

    try:
        response = requests.post(DISCORD_WEBHOOK, json=body, timeout=8)
        return {
            "sent": response.ok,
            "status_code": response.status_code,
            "ok": response.ok,
        }
    except requests.RequestException as error:
        return {"sent": False, "error": str(error)}


def _send_discord_tiny_alert(message: str):
    if not DISCORD_WEBHOOK:
        return {"sent": False, "reason": "DISCORD_WEBHOOK not configured"}

    body = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK, json=body, timeout=8)
        return {
            "sent": response.ok,
            "status_code": response.status_code,
            "ok": response.ok,
        }
    except requests.RequestException as error:
        return {"sent": False, "error": str(error)}


def _forward_to_vega(payload: dict, normalized: dict):
    if not VEGA_BOT_WEBHOOK_URL:
        return {
            "forwarded": False,
            "reason": "VEGA_BOT_WEBHOOK_URL not configured",
        }

    forward_body = {
        "source": "tradingview",
        "received_at": datetime.now().isoformat(),
        "payload": _redact_payload(payload),
        "normalized": normalized,
    }

    try:
        response = requests.post(
            VEGA_BOT_WEBHOOK_URL,
            json=forward_body,
            timeout=8,
        )
        return {
            "forwarded": response.ok,
            "status_code": response.status_code,
            "ok": response.ok,
        }
    except requests.RequestException as error:
        return {"forwarded": False, "error": str(error)}


def _cors_headers(origin: str = ALLOWED_ORIGIN):
    allowed_headers = "Content-Type, Authorization, x-api-key"
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": allowed_headers,
    }


def _response(status: int, body: dict, origin: str = ALLOWED_ORIGIN):
    return {
        "statusCode": status,
        "headers": _cors_headers(origin),
        "body": json.dumps(body),
    }


def handler(request):
    """Main request handler for Vercel serverless functions"""

    path = getattr(request, "path", "/")
    path_only = path.split("?", 1)[0]
    method = getattr(request, "method", "GET").upper()
    headers = _request_headers(request)

    # Preflight
    if method == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": _cors_headers(),
            "body": "",
        }

    # Public: Health
    if path_only in ("/", "/health"):
        return _response(
            200,
            {
                "status": "healthy",
                "service": "bentley-budget-bot-api",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
            },
        )

    # Public: Status
    if path_only == "/status":
        return _response(
            200,
            {
                "service": "BentleyBudgetBot API",
                "status": "operational",
                "endpoints": {
                    "health": "/health",
                    "status": "/status",
                    "portfolio": "/api/portfolio",
                    "tradingview_alert": "/api/vega/tradingview-alert",
                },
                "timestamp": datetime.now().isoformat(),
            },
        )

    # TradingView webhook for Vega automation
    if path_only == "/api/vega/tradingview-alert":
        if method != "POST":
            return _response(405, {"error": "Method not allowed. Use POST."})

        query_params = _request_query_params(request, path)
        payload, raw_text = _request_json_body(request)
        normalized = _normalize_tradingview_payload(payload)

        provided_secret = (
            query_params.get("secret")
            or payload.get("secret")
            or payload.get("passphrase")
            or payload.get("token")
        ) if isinstance(payload, dict) else query_params.get("secret")
        provided_api_key = headers.get("x-api-key")

        if TRADINGVIEW_WEBHOOK_SECRET:
            if provided_secret != TRADINGVIEW_WEBHOOK_SECRET:
                return _response(401, {"error": "Unauthorized webhook secret"})
        elif API_KEY and provided_api_key != API_KEY:
            return _response(401, {"error": "Unauthorized"})

        execution_mode = "paper"
        if isinstance(payload, dict):
            mode_value = (
                payload.get("mode")
                or payload.get("trade_mode")
                or payload.get("execution_mode")
                or "paper"
            )
            execution_mode = str(mode_value).strip().lower()

        if execution_mode not in {"paper", "live"}:
            return _response(
                400,
                {
                    "error": "Invalid execution mode",
                    "allowed_modes": ["paper", "live"],
                },
            )

        live_key = None
        if isinstance(payload, dict):
            live_key = payload.get("live_key")
        if not live_key:
            live_key = query_params.get("live_key")
        if not live_key:
            live_key = headers.get("x-live-key")

        if execution_mode == "live":
            if _is_truthy(VEGA_PAPER_ONLY):
                symbol = normalized.get("symbol") or "UNKNOWN"
                timeframe = normalized.get("timeframe") or "n/a"
                _send_discord_tiny_alert(
                    "⚠️ Blocked live TradingView request "
                    f"({symbol}, TF {timeframe}): VEGA_PAPER_ONLY=true"
                )
                return _response(
                    403,
                    {
                        "error": "Live mode disabled",
                        "message": "VEGA_PAPER_ONLY is enabled",
                    },
                )

            if VEGA_LIVE_MODE_KEY and live_key != VEGA_LIVE_MODE_KEY:
                return _response(
                    401,
                    {
                        "error": "Unauthorized live mode key",
                    },
                )

        normalized["execution_mode"] = execution_mode

        vega_result = _forward_to_vega(payload, normalized)

        send_discord = False
        if isinstance(payload, dict):
            send_discord = bool(payload.get("send_discord", False))
        if send_discord:
            discord_result = _send_discord_alert(normalized)
        else:
            discord_result = {
                "sent": False,
                "reason": "send_discord not enabled in payload",
            }

        return _response(
            200,
            {
                "status": "received",
                "route": "/api/vega/tradingview-alert",
                "received_at": datetime.now().isoformat(),
                "execution_mode": execution_mode,
                "normalized": normalized,
                "forward": vega_result,
                "discord": discord_result,
                "raw_message_present": bool(raw_text),
            },
            origin="*",
        )

    # Protect all /api/* endpoints with x-api-key if configured
    if path_only.startswith("/api/") and API_KEY:
        provided = headers.get("x-api-key")
        if provided != API_KEY:
            return _response(401, {"error": "Unauthorized"})

    # Example API: Portfolio placeholder
    if path_only == "/api/portfolio":
        return _response(
            200,
            {
                "message": "Portfolio endpoint placeholder",
                "note": "Connect to Streamlit frontend for portfolio data",
            },
        )

    # Plaid Link Token endpoint
    if path_only == "/api/plaid/link_token":
        try:
            # Get link_token from Streamlit session via environment
            # In production, this would call Plaid API
            link_token = os.getenv("PLAID_LINK_TOKEN")
            if not link_token:
                return _response(
                    500,
                    {
                        "error": (
                            "Link token not available. "
                            "Create one in Streamlit first."
                        )
                    },
                )
            return _response(200, {"link_token": link_token})
        except (OSError, RuntimeError, ValueError, TypeError) as e:
            return _response(500, {"error": str(e)})

    # 404
    return _response(
        404,
        {
            "error": "Endpoint not found",
            "path": path_only,
            "available_endpoints": [
                "/health",
                "/status",
                "/api/portfolio",
                "/api/plaid/link_token",
                "/api/vega/tradingview-alert",
            ],
        },
    )


# Export for Vercel
app = handler
