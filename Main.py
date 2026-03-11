import os
from functools import lru_cache
from typing import Literal, Optional, Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
import requests

from frontend.components.ibkr_gateway_client import (
    GatewayConfig,
    IBKRGatewayClient,
)

app = FastAPI(
    title="Bentley Budget Bot API",
    version="0.1.0",
    description="Minimal FastAPI service for Bentley Budget Bot.",
)


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
        except Exception:
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

    except Exception as exc:
        result["error"] = str(exc)
        return result


@app.get("/")
async def root():
    return {"message": "Bentley Budget Bot!"}


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


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

    This is intentionally verbose so same-day setup issues can be resolved fast.
    """
    configured = os.getenv("IBKR_GATEWAY_URL", "https://localhost:5000").strip()

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
            "No valid IBKR CPAPI endpoint detected. Current localhost:5000 often maps to Docker in this workspace."
        )
        guidance.append(
            "Set IBKR_GATEWAY_URL to the actual Client Portal API URL, then restart API."
        )
        guidance.append(
            "Expected auth endpoint: <IBKR_GATEWAY_URL>/v1/api/iserver/auth/status returning JSON with authenticated field."
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
        raise HTTPException(status_code=503, detail="IBKR gateway unreachable")
    accounts = client.get_accounts()
    if not accounts:
        raise HTTPException(status_code=502, detail="No IBKR accounts returned")
    return {"accounts": accounts}


@app.post("/ibkr/forex/resolve")
async def ibkr_forex_resolve(payload: IBKRResolveForexRequest):
    client = get_ibkr_client()
    if not client.start_gateway():
        raise HTTPException(status_code=503, detail="IBKR gateway unreachable")
    conid = client.resolve_forex_conid(payload.symbol, exchange=payload.exchange)
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
        raise HTTPException(status_code=503, detail="IBKR gateway unreachable")

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
        raise HTTPException(status_code=503, detail="IBKR gateway unreachable")

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
        raise HTTPException(status_code=503, detail="IBKR gateway unreachable")

    acct = account_id or client.config.account_id
    if not acct:
        raise HTTPException(status_code=400, detail="IBKR account_id is required")

    result = client.api_request(f"/portfolio/{acct}/positions/0")
    if result is None:
        raise HTTPException(status_code=502, detail="IBKR positions request failed")

    return {
        "account_id": acct,
        "positions": result,
    }