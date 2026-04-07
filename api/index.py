"""
Vercel Serverless API Handler for BentleyBudgetBot
Adds CORS and simple API key auth for /api/* endpoints.
"""

import json
import os
import time
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import requests

try:
    from scripts.load_screener_csv import (
        load_bot_config,
        load_screener_csv,
        resolve_screener_path,
    )

    BOT_UNIVERSE_LOADER_AVAILABLE = True
    BOT_UNIVERSE_LOADER_ERROR = None
except (ImportError, OSError, ValueError) as error:
    BOT_UNIVERSE_LOADER_AVAILABLE = False
    BOT_UNIVERSE_LOADER_ERROR = str(error)


ALLOWED_ORIGIN = os.getenv("FRONTEND_ORIGIN", "https://bbbot305.streamlit.app")
API_KEY = os.getenv("API_GATEWAY_KEY")
TRADINGVIEW_WEBHOOK_SECRET = os.getenv("TRADINGVIEW_WEBHOOK_SECRET")
VEGA_BOT_WEBHOOK_URL = os.getenv("VEGA_BOT_WEBHOOK_URL")
DISCORD_WEBHOOK = (
    os.getenv("DISCORD_WEBHOOK")
    or os.getenv("DISCORD_WEBHOOK_PROD")
)
REQUIRED_DISCORD_INDICATORS = ("FVFI", "ROVL")
VEGA_PAPER_ONLY = os.getenv("VEGA_PAPER_ONLY", "true").strip().lower()
VEGA_LIVE_MODE_KEY = os.getenv("VEGA_LIVE_MODE_KEY")
VEGA_BLOCKED_LIVE_ALERT_COOLDOWN_SECONDS = os.getenv(
    "VEGA_BLOCKED_LIVE_ALERT_COOLDOWN_SECONDS",
    "300",
)

BLOCKED_LIVE_ALERT_LAST_SENT = {}
BOT_UNIVERSE_CACHE = {}


def _is_truthy(value):
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _as_non_negative_int(value, default: int) -> int:
    try:
        parsed = int(str(value).strip())
        return parsed if parsed >= 0 else default
    except (TypeError, ValueError):
        return default


def _should_send_blocked_live_alert(symbol: str, timeframe: str) -> bool:
    cooldown = _as_non_negative_int(
        VEGA_BLOCKED_LIVE_ALERT_COOLDOWN_SECONDS,
        default=300,
    )
    if cooldown == 0:
        return True

    key = f"{symbol}:{timeframe}"
    now = time.time()
    last_sent = BLOCKED_LIVE_ALERT_LAST_SENT.get(key)
    if last_sent is not None and (now - last_sent) < cooldown:
        return False

    BLOCKED_LIVE_ALERT_LAST_SENT[key] = now
    return True


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


def _normalize_symbol_token(value):
    token = str(value or "").strip().upper()
    if not token:
        return None

    if ":" not in token:
        return token

    exchange, symbol = token.split(":", 1)
    if not symbol:
        return None
    if exchange == "TSX":
        return f"{symbol}.TO"
    if exchange == "TSXV":
        return f"{symbol}.V"
    return symbol


def _load_bot_universe(bot_name: str):
    requested_bot = str(bot_name or "Vega_Bot").strip() or "Vega_Bot"
    config_path = os.getenv("BOT_CONFIG_PATH", "bentley-bot/config/bots")
    cache_key = f"{requested_bot}|{config_path}"
    cached = BOT_UNIVERSE_CACHE.get(cache_key)
    if cached is not None:
        return cached

    if not BOT_UNIVERSE_LOADER_AVAILABLE:
        result = {
            "loaded": False,
            "bot": requested_bot,
            "reason": (
                BOT_UNIVERSE_LOADER_ERROR
                or "bot universe loader unavailable"
            ),
            "symbols": set(),
            "universe": "",
            "screener_file": "",
        }
        BOT_UNIVERSE_CACHE[cache_key] = result
        return result

    try:
        bot_config = load_bot_config(requested_bot, config_path=config_path)
        screener_path = resolve_screener_path(
            bot_config,
            config_path=config_path,
        )
        symbols = {
            normalized
            for normalized in (
                _normalize_symbol_token(symbol)
                for symbol in load_screener_csv(screener_path)
            )
            if normalized
        }
        result = {
            "loaded": True,
            "bot": str(bot_config.get("bot_name") or requested_bot),
            "display_bot": str(
                bot_config.get("bot_display_name")
                or bot_config.get("bot_name")
                or requested_bot
            ),
            "universe": str(bot_config.get("universe") or ""),
            "screener_file": str(screener_path),
            "symbols": symbols,
        }
    except (FileNotFoundError, OSError, ValueError) as error:
        result = {
            "loaded": False,
            "bot": requested_bot,
            "reason": str(error),
            "symbols": set(),
            "universe": "",
            "screener_file": "",
        }

    BOT_UNIVERSE_CACHE[cache_key] = result
    return result


def _validate_symbol_for_bot(normalized: dict):
    bot_name = normalized.get("bot") or "Vega_Bot"
    symbol = _normalize_symbol_token(normalized.get("symbol"))
    if not symbol:
        return {
            "valid": False,
            "bot": bot_name,
            "reason": "missing symbol",
        }

    universe_info = _load_bot_universe(bot_name)
    if not universe_info.get("loaded"):
        return {
            "valid": False,
            "bot": bot_name,
            "symbol": symbol,
            "reason": (
                universe_info.get("reason")
                or "unable to load bot universe"
            ),
            "universe": universe_info.get("universe") or "",
            "screener_file": universe_info.get("screener_file") or "",
        }

    allowed_symbols = universe_info.get("symbols") or set()
    if not allowed_symbols:
        return {
            "valid": False,
            "bot": universe_info.get("bot") or bot_name,
            "symbol": symbol,
            "reason": "configured universe has no symbols",
            "universe": universe_info.get("universe") or "",
            "screener_file": universe_info.get("screener_file") or "",
        }

    if symbol not in allowed_symbols:
        return {
            "valid": False,
            "bot": universe_info.get("bot") or bot_name,
            "symbol": symbol,
            "reason": "symbol not in configured universe",
            "universe": universe_info.get("universe") or "",
            "screener_file": universe_info.get("screener_file") or "",
        }

    return {
        "valid": True,
        "bot": universe_info.get("bot") or bot_name,
        "symbol": symbol,
        "universe": universe_info.get("universe") or "",
        "screener_file": universe_info.get("screener_file") or "",
    }


def _normalize_tradingview_payload(payload):
    if not isinstance(payload, dict):
        return {}

    bot_name = (
        payload.get("bot")
        or payload.get("bot_name")
        or payload.get("runtime_name")
        or "Vega_Bot"
    )
    symbol = payload.get("symbol") or payload.get("ticker")
    side = (
        payload.get("action")
        or payload.get("side")
        or payload.get("strategy.order.action")
    )
    timeframe = payload.get("timeframe") or payload.get("interval")

    return {
        "bot": bot_name,
        "fund": (
            payload.get("fund")
            or payload.get("fund_name")
            or "Mansa Retail"
        ),
        "symbol": symbol,
        "side": side,
        "timeframe": timeframe,
        "strategy": (
            payload.get("strategy")
            or payload.get("strategy_name")
            or "Breakout Strategy"
        ),
        "configured_universe": payload.get("universe"),
        "price": payload.get("price") or payload.get("close"),
        "alert_name": payload.get("alert_name") or payload.get("name"),
        "fvfi": (
            payload.get("FVFI")
            or payload.get("fvfi")
            or payload.get("volume_flow_indicator")
        ),
        "rovl": (
            payload.get("ROVL")
            or payload.get("rovl")
            or payload.get("relative_volume")
        ),
    }


def _missing_required_discord_indicators(normalized: dict):
    missing = []
    if normalized.get("fvfi") in (None, ""):
        missing.append("FVFI")
    if normalized.get("rovl") in (None, ""):
        missing.append("ROVL")
    return missing


def _send_discord_alert(normalized: dict):
    if not DISCORD_WEBHOOK:
        return {"sent": False, "reason": "DISCORD_WEBHOOK not configured"}

    missing_indicators = _missing_required_discord_indicators(normalized)
    if missing_indicators:
        return {
            "sent": False,
            "reason": "missing required indicators",
            "missing": missing_indicators,
        }

    bot_name = normalized.get("bot") or "Vega_Bot"
    fund = normalized.get("fund") or "Mansa Retail"
    symbol = normalized.get("symbol") or "UNKNOWN"
    side = normalized.get("side") or "signal"
    timeframe = normalized.get("timeframe") or "n/a"
    strategy = normalized.get("strategy") or "Breakout Strategy"
    universe = normalized.get("configured_universe") or "n/a"
    price = normalized.get("price")
    fvfi = normalized.get("fvfi")
    rovl = normalized.get("rovl")

    content = (
        f"📡 Trading Signal Alert | {bot_name} | {strategy} | {symbol} | "
        f"{side} | TF: {timeframe}"
    )
    if price is not None:
        content += f" | Price: {price}"
    content += f" | Universe: {universe}"
    content += f" | FVFI: {fvfi} | ROVL: {rovl}"

    body = {
        "content": content,
        "embeds": [
            {
                "title": "Trading Signal Alert",
                "description": (
                    "Webhook received by Bentley bot alert endpoint"
                ),
                "fields": [
                    {"name": "Bot", "value": str(bot_name), "inline": True},
                    {"name": "Fund", "value": str(fund), "inline": True},
                    {
                        "name": "Strategy",
                        "value": str(strategy),
                        "inline": False,
                    },
                    {"name": "Symbol", "value": str(symbol), "inline": True},
                    {"name": "Side", "value": str(side), "inline": True},
                    {
                        "name": "Timeframe",
                        "value": str(timeframe),
                        "inline": True,
                    },
                    {
                        "name": "Universe",
                        "value": str(universe),
                        "inline": False,
                    },
                    {"name": "FVFI", "value": str(fvfi), "inline": True},
                    {"name": "ROVL", "value": str(rovl), "inline": True},
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


def _forward_to_vega(payload, normalized: dict):
    bot_name = str(normalized.get("bot") or "Vega_Bot")
    if bot_name not in {"Vega", "Vega_Bot"}:
        return {
            "forwarded": False,
            "reason": f"No bot execution forward configured for {bot_name}",
        }

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
                    "generic_tradingview_alert": "/api/tradingview-alert",
                    "tradingview_alert": "/api/vega/tradingview-alert",
                },
                "timestamp": datetime.now().isoformat(),
            },
        )

    # TradingView webhook for bot automation
    if path_only in {"/api/vega/tradingview-alert", "/api/tradingview-alert"}:
        if method != "POST":
            return _response(405, {"error": "Method not allowed. Use POST."})

        query_params = _request_query_params(request, path)
        payload, raw_text = _request_json_body(request)
        payload_dict = payload if isinstance(payload, dict) else {}
        normalized = _normalize_tradingview_payload(payload_dict)

        provided_secret = (
            query_params.get("secret")
            or payload_dict.get("secret")
            or payload_dict.get("passphrase")
            or payload_dict.get("token")
        )
        provided_api_key = headers.get("x-api-key")

        if TRADINGVIEW_WEBHOOK_SECRET:
            if provided_secret != TRADINGVIEW_WEBHOOK_SECRET:
                return _response(401, {"error": "Unauthorized webhook secret"})
        elif API_KEY and provided_api_key != API_KEY:
            return _response(401, {"error": "Unauthorized"})

        universe_validation = _validate_symbol_for_bot(normalized)
        normalized["symbol"] = universe_validation.get(
            "symbol",
            normalized.get("symbol"),
        )
        normalized["configured_universe"] = universe_validation.get(
            "universe",
            normalized.get("configured_universe"),
        )
        if not universe_validation.get("valid"):
            return _response(
                422,
                {
                    "error": "Symbol rejected by bot universe guard",
                    "validation": universe_validation,
                    "normalized": normalized,
                },
            )

        execution_mode = "paper"
        mode_value = (
            payload_dict.get("mode")
            or payload_dict.get("trade_mode")
            or payload_dict.get("execution_mode")
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
        live_key = payload_dict.get("live_key")
        if not live_key:
            live_key = query_params.get("live_key")
        if not live_key:
            live_key = headers.get("x-live-key")

        if execution_mode == "live":
            symbol = normalized.get("symbol") or "UNKNOWN"
            timeframe = normalized.get("timeframe") or "n/a"

            if _is_truthy(VEGA_PAPER_ONLY):
                if _should_send_blocked_live_alert(symbol, timeframe):
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
                if _should_send_blocked_live_alert(symbol, timeframe):
                    _send_discord_tiny_alert(
                        "⚠️ Blocked live TradingView request "
                        f"({symbol}, TF {timeframe}): invalid live key"
                    )
                return _response(
                    401,
                    {
                        "error": "Unauthorized live mode key",
                    },
                )

        normalized["execution_mode"] = execution_mode

        vega_result = _forward_to_vega(payload_dict, normalized)

        send_discord = bool(payload_dict.get("send_discord", False))
        missing_discord_indicators = _missing_required_discord_indicators(
            normalized
        )
        if send_discord and missing_discord_indicators:
            return _response(
                400,
                {
                    "error": "Missing required Discord indicators",
                    "required_indicators": list(REQUIRED_DISCORD_INDICATORS),
                    "missing": missing_discord_indicators,
                    "normalized": normalized,
                },
            )
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
                "route": path_only,
                "received_at": datetime.now().isoformat(),
                "execution_mode": execution_mode,
                "normalized": normalized,
                "validation": universe_validation,
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
