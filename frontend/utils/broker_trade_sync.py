"""
Broker trade synchronization utilities.

This module fetches recent broker orders/trades and stores them in trades_history
so the Trading Bot Trade History tab reflects executed activity across brokers.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging
import os
from typing import Any, Iterable

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from frontend.utils.secrets_helper import get_mysql_url
from frontend.utils.discord_alpaca import send_discord_trade_notification

logger = logging.getLogger(__name__)


@dataclass
class SyncStats:
    broker: str
    inserted: int = 0
    skipped: int = 0
    notified: int = 0
    errors: int = 0


def _parse_timestamp(value: Any) -> datetime:
    if value is None:
        return datetime.utcnow()
    if isinstance(value, datetime):
        return value

    text_value = str(value).strip()
    if not text_value:
        return datetime.utcnow()

    # Handle trailing Z used by many APIs.
    if text_value.endswith("Z"):
        text_value = text_value[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(text_value)
    except ValueError:
        pass

    # Fallback for common API date format.
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text_value, fmt)
        except ValueError:
            continue

    return datetime.utcnow()


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _get_engine() -> Engine:
    return create_engine(get_mysql_url())


def _trade_exists(conn, order_id: str) -> bool:
    if not order_id:
        return False
    row = conn.execute(
        text("SELECT 1 FROM trades_history WHERE order_id = :order_id LIMIT 1"),
        {"order_id": order_id},
    ).fetchone()
    return row is not None


def _insert_trade_row(
    conn,
    *,
    ticker: str,
    action: str,
    shares: int,
    price: float,
    value: float,
    timestamp: datetime,
    status: str,
    order_id: str,
    strategy: str,
) -> None:
    conn.execute(
        text(
            """
            INSERT INTO trades_history
            (ticker, action, shares, price, value, timestamp, status, order_id, strategy)
            VALUES
            (:ticker, :action, :shares, :price, :value, :timestamp, :status, :order_id, :strategy)
            """
        ),
        {
            "ticker": ticker,
            "action": action,
            "shares": shares,
            "price": price,
            "value": value,
            "timestamp": timestamp,
            "status": status,
            "order_id": order_id,
            "strategy": strategy,
        },
    )


def sync_alpaca_orders(alpaca_connector) -> SyncStats:
    stats = SyncStats(broker="Alpaca")

    try:
        orders = alpaca_connector.get_orders(status="closed") or []
    except Exception as exc:
        logger.error("Failed to fetch Alpaca orders: %s", exc)
        stats.errors += 1
        return stats

    if not orders:
        return stats

    webhook_url = (
        os.getenv("DISCORD_BOT_TALK_WEBHOOK", "").strip()
        or os.getenv("DISCORD_ALPACA_WEBHOOK", "").strip()
    )

    engine = _get_engine()
    with engine.begin() as conn:
        for order in orders:
            try:
                symbol = str(order.get("symbol", "")).strip().upper()
                side = str(order.get("side", "")).strip().upper()
                order_id = str(order.get("id", "")).strip()
                order_status = str(order.get("status", "")).strip().upper() or "EXECUTED"

                qty = _to_int(order.get("filled_qty") or order.get("qty"))
                if not symbol or side not in {"BUY", "SELL"} or qty <= 0:
                    stats.skipped += 1
                    continue

                price = _to_float(order.get("filled_avg_price") or order.get("limit_price"))
                if price <= 0:
                    stats.skipped += 1
                    continue

                if order_id and _trade_exists(conn, order_id):
                    stats.skipped += 1
                    continue

                ts = _parse_timestamp(
                    order.get("filled_at")
                    or order.get("submitted_at")
                    or order.get("created_at")
                )
                value = round(float(qty) * price, 4)

                _insert_trade_row(
                    conn,
                    ticker=symbol,
                    action=side,
                    shares=qty,
                    price=price,
                    value=value,
                    timestamp=ts,
                    status=order_status,
                    order_id=order_id,
                    strategy="alpaca",
                )
                stats.inserted += 1

                if order_status in {"FILLED", "EXECUTED"}:
                    if send_discord_trade_notification(
                        symbol=symbol,
                        side=side.lower(),
                        qty=qty,
                        order_type=str(order.get("type", "market")),
                        limit_price=price,
                        status=order_status,
                        webhook_url=webhook_url or None,
                    ):
                        stats.notified += 1
            except Exception as exc:
                logger.error("Failed to sync Alpaca order: %s", exc)
                stats.errors += 1

    return stats


def _iter_ibkr_trades(raw: Any) -> Iterable[dict[str, Any]]:
    if isinstance(raw, dict):
        # Some responses return {'trades': [...]} or {'orders': [...]}.
        for key in ("trades", "orders"):
            value = raw.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        yield item
        return

    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                yield item


def sync_ibkr_trades(ibkr_connector) -> SyncStats:
    stats = SyncStats(broker="IBKR")

    try:
        raw = ibkr_connector.get_trades() or []
    except Exception as exc:
        logger.error("Failed to fetch IBKR trades: %s", exc)
        stats.errors += 1
        return stats

    engine = _get_engine()
    with engine.begin() as conn:
        for trade in _iter_ibkr_trades(raw):
            try:
                symbol = str(
                    trade.get("symbol")
                    or trade.get("contractDesc")
                    or trade.get("conidEx")
                    or ""
                ).strip().upper()
                side = str(trade.get("side") or trade.get("action") or "").strip().upper()
                side = "BUY" if side.startswith("B") else "SELL" if side.startswith("S") else ""

                order_id = str(
                    trade.get("execution_id")
                    or trade.get("orderId")
                    or trade.get("id")
                    or ""
                ).strip()

                qty = _to_int(trade.get("size") or trade.get("quantity") or trade.get("qty"))
                price = _to_float(trade.get("price") or trade.get("avgPrice") or trade.get("tradePrice"))
                if not symbol or side not in {"BUY", "SELL"} or qty <= 0 or price <= 0:
                    stats.skipped += 1
                    continue

                if order_id and _trade_exists(conn, order_id):
                    stats.skipped += 1
                    continue

                ts = _parse_timestamp(
                    trade.get("trade_time")
                    or trade.get("executionTime")
                    or trade.get("time")
                )
                value = round(float(qty) * price, 4)

                _insert_trade_row(
                    conn,
                    ticker=symbol,
                    action=side,
                    shares=qty,
                    price=price,
                    value=value,
                    timestamp=ts,
                    status="EXECUTED",
                    order_id=order_id,
                    strategy="ibkr",
                )
                stats.inserted += 1
            except Exception as exc:
                logger.error("Failed to sync IBKR trade: %s", exc)
                stats.errors += 1

    return stats


def sync_mt5_positions_as_trades(mt5_connector, strategy_name: str = "mt5") -> SyncStats:
    """
    MT5 REST bridge currently exposes positions reliably in this project.
    We persist open positions as trade rows so they appear in dashboard history.
    """
    stats = SyncStats(broker="MT5")

    try:
        positions = mt5_connector.get_positions() or []
    except Exception as exc:
        logger.error("Failed to fetch MT5 positions: %s", exc)
        stats.errors += 1
        return stats

    engine = _get_engine()
    with engine.begin() as conn:
        for pos in positions:
            try:
                symbol = str(getattr(pos, "symbol", "")).strip().upper()
                side = str(getattr(pos, "type", "")).strip().upper()
                side = "BUY" if side.startswith("B") else "SELL" if side.startswith("S") else ""
                order_id = str(getattr(pos, "ticket", "") or "").strip()

                volume = _to_float(getattr(pos, "volume", 0.0))
                shares = max(_to_int(volume), 1 if volume > 0 else 0)
                price = _to_float(getattr(pos, "current_price", 0.0) or getattr(pos, "open_price", 0.0))

                if not symbol or side not in {"BUY", "SELL"} or shares <= 0 or price <= 0:
                    stats.skipped += 1
                    continue

                if order_id and _trade_exists(conn, order_id):
                    stats.skipped += 1
                    continue

                ts = _parse_timestamp(getattr(pos, "open_time", None))
                value = round(float(shares) * price, 4)

                _insert_trade_row(
                    conn,
                    ticker=symbol,
                    action=side,
                    shares=shares,
                    price=price,
                    value=value,
                    timestamp=ts,
                    status="OPEN",
                    order_id=order_id,
                    strategy=strategy_name,
                )
                stats.inserted += 1
            except Exception as exc:
                logger.error("Failed to sync MT5 position: %s", exc)
                stats.errors += 1

    return stats


def sync_connected_brokers(brokers: dict[str, Any]) -> list[SyncStats]:
    """Sync all connected brokers and return per-broker stats."""
    results: list[SyncStats] = []

    alpaca = brokers.get("alpaca")
    if alpaca is not None:
        results.append(sync_alpaca_orders(alpaca))

    ibkr = brokers.get("ibkr")
    if ibkr is not None:
        results.append(sync_ibkr_trades(ibkr))

    mt5 = brokers.get("mt5")
    if mt5 is not None:
        results.append(sync_mt5_positions_as_trades(mt5, strategy_name="mt5"))

    axi = brokers.get("axi")
    if axi is not None:
        results.append(sync_mt5_positions_as_trades(axi, strategy_name="axi_mt5"))

    return results
