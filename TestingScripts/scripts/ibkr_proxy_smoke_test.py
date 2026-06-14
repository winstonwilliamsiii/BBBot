"""
Smoke test for canonical Python IBKR proxy routes.

Default behavior is non-trading:
- Checks API health
- Checks IBKR health
- Fetches accounts
- Resolves strict FOREX conid

Use --place-order to place a live order through /ibkr/forex/order.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

import requests


def _parse_json_response(resp: requests.Response) -> Dict[str, Any]:
    try:
        return resp.json()
    except Exception as exc:
        snippet = (resp.text or "")[:400]
        raise RuntimeError(
            "Non-JSON response from "
            f"{resp.url} status={resp.status_code} body={snippet!r}"
        ) from exc


def _get_json(url: str, timeout: int) -> Dict[str, Any]:
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return _parse_json_response(resp)


def _post_json(url: str, payload: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    return _parse_json_response(resp)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="IBKR proxy smoke test (safe by default)"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Canonical Python API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--account-id",
        default="U14774118",
        help="IBKR account ID (default: U14774118)",
    )
    parser.add_argument(
        "--symbol",
        default="EURUSD",
        help="FOREX symbol for strict conid resolution (default: EURUSD)",
    )
    parser.add_argument(
        "--side",
        choices=["BUY", "SELL"],
        default="BUY",
        help="Order side if --place-order is used",
    )
    parser.add_argument(
        "--quantity",
        type=float,
        default=1000,
        help="Order quantity if --place-order is used",
    )
    parser.add_argument(
        "--place-order",
        action="store_true",
        help="Actually place a FOREX order through /ibkr/forex/order",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="HTTP timeout seconds (default: 15)",
    )

    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    report: Dict[str, Any] = {
        "base_url": base,
        "account_id": args.account_id,
        "symbol": args.symbol,
        "checks": {},
        "order": None,
    }

    try:
        report["checks"]["api_health"] = _get_json(f"{base}/healthz", args.timeout)
        report["checks"]["ibkr_ping"] = _get_json(f"{base}/ibkr/ping", args.timeout)
        report["checks"]["ibkr_health"] = _get_json(f"{base}/ibkr/health", args.timeout)
        report["checks"]["accounts"] = _get_json(f"{base}/ibkr/accounts", args.timeout)

        resolve_payload = {"symbol": args.symbol, "exchange": "IDEALPRO"}
        report["checks"]["resolve_forex"] = _post_json(
            f"{base}/ibkr/forex/resolve", resolve_payload, args.timeout
        )

        if args.place_order:
            order_payload = {
                "symbol": args.symbol,
                "side": args.side,
                "quantity": args.quantity,
                "account_id": args.account_id,
                "exchange": "IDEALPRO",
                "order_type": "MKT",
                "tif": "DAY",
            }
            report["order"] = _post_json(
                f"{base}/ibkr/forex/order", order_payload, args.timeout
            )
        else:
            report["order"] = "skipped (safe mode)"

        print(json.dumps(report, indent=2))
        return 0

    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        body = exc.response.text if exc.response is not None else str(exc)
        report["error"] = {
            "type": "http_error",
            "status_code": status,
            "message": body,
        }
        print(json.dumps(report, indent=2))
        return 2

    except Exception as exc:
        report["error"] = {"type": "runtime_error", "message": str(exc)}
        print(json.dumps(report, indent=2))
        return 3


if __name__ == "__main__":
    sys.exit(main())
