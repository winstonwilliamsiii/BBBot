"""SQLite persistence for Cosmic signals and premium subscribers."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "bentley_signals.sqlite3"


def _database_path() -> Path:
    path = Path(os.getenv("BENTLEY_SIGNAL_DB_PATH", str(_DEFAULT_DB)))
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(_database_path(), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    return connection


#: Supported subscription tiers, enforced across authentication and rate limiting.
VALID_TIERS = ("basic", "pro", "institutional")

#: Supported delivery methods for the DeliveryRouter fan-out.
VALID_DELIVERY_METHODS = ("webhook", "api", "websocket", "email")


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_name TEXT NOT NULL,
            symbol TEXT NOT NULL,
            cosmic_score REAL NOT NULL,
            decision TEXT NOT NULL,
            heads TEXT NOT NULL,
            mode TEXT NOT NULL,
            metadata TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_signals_bot_timestamp
            ON signals (bot_name, timestamp DESC);
        CREATE TABLE IF NOT EXISTS subscribers (
            subscriber_id TEXT PRIMARY KEY,
            email TEXT,
            tier TEXT NOT NULL,
            api_key TEXT NOT NULL UNIQUE,
            delivery_method TEXT NOT NULL,
            webhook_url TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_subscribers_api_key
            ON subscribers (api_key);
        CREATE TABLE IF NOT EXISTS delivery_dead_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscriber_id TEXT NOT NULL,
            delivery_method TEXT NOT NULL,
            payload TEXT NOT NULL,
            error TEXT NOT NULL,
            attempts INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_dead_letters_subscriber
            ON delivery_dead_letters (subscriber_id, created_at DESC);
        """
    )
    # Defensive migration for pre-existing databases created before the
    # `email` / `created_at` columns were added to the subscribers table.
    existing_columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(subscribers)").fetchall()
    }
    if "email" not in existing_columns:
        connection.execute("ALTER TABLE subscribers ADD COLUMN email TEXT")
    if "created_at" not in existing_columns:
        connection.execute(
            "ALTER TABLE subscribers ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'))"
        )


def store_signal(signal_payload: dict[str, Any]) -> dict[str, Any]:
    """Persist and return a normalized signal payload."""
    payload = {
        "bot": str(signal_payload["bot"]),
        "symbol": str(signal_payload["symbol"]),
        "cosmic_score": float(signal_payload["cosmic_score"]),
        "decision": str(signal_payload["decision"]),
        "heads": signal_payload.get("heads", []),
        "mode": str(signal_payload.get("mode", "paper")),
        "metadata": signal_payload.get("metadata", {}),
        "timestamp": signal_payload.get("timestamp") or datetime.now(timezone.utc).isoformat(),
    }
    with _connect() as connection:
        _ensure_schema(connection)
        connection.execute(
            """
            INSERT INTO signals
                (bot_name, symbol, cosmic_score, decision, heads, mode, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["bot"],
                payload["symbol"],
                payload["cosmic_score"],
                payload["decision"],
                json.dumps(payload["heads"]),
                payload["mode"],
                json.dumps(payload["metadata"]),
                payload["timestamp"],
            ),
        )
    return payload


def fetch_latest_signal(bot_name: str) -> dict[str, Any] | None:
    """Fetch the newest stored signal for a bot, or ``None`` if unavailable."""
    with _connect() as connection:
        _ensure_schema(connection)
        row = connection.execute(
            """
            SELECT bot_name, symbol, cosmic_score, decision, heads, mode, metadata, timestamp
            FROM signals
            WHERE lower(bot_name) = lower(?)
            ORDER BY timestamp DESC, id DESC
            LIMIT 1
            """,
            (bot_name,),
        ).fetchone()
    if row is None:
        return None
    return {
        "bot": row["bot_name"],
        "symbol": row["symbol"],
        "cosmic_score": row["cosmic_score"],
        "decision": row["decision"],
        "heads": json.loads(row["heads"]),
        "mode": row["mode"],
        "metadata": json.loads(row["metadata"]),
        "timestamp": row["timestamp"],
    }


_SUBSCRIBER_COLUMNS = (
    "subscriber_id, email, tier, api_key, delivery_method, webhook_url, status, created_at"
)


def list_active_subscribers() -> list[dict[str, Any]]:
    """Return active subscribers eligible for signal delivery."""
    with _connect() as connection:
        _ensure_schema(connection)
        rows = connection.execute(
            f"""
            SELECT {_SUBSCRIBER_COLUMNS}
            FROM subscribers
            WHERE status = 'active'
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_subscriber_by_api_key(api_key: str) -> dict[str, Any] | None:
    """Look up a single subscriber by their API key, regardless of status."""
    if not api_key:
        return None
    with _connect() as connection:
        _ensure_schema(connection)
        row = connection.execute(
            f"""
            SELECT {_SUBSCRIBER_COLUMNS}
            FROM subscribers
            WHERE api_key = ?
            """,
            (api_key,),
        ).fetchone()
    return dict(row) if row is not None else None


def register_subscriber(subscriber: dict[str, Any]) -> None:
    """Create or update a subscriber registry entry."""
    with _connect() as connection:
        _ensure_schema(connection)
        connection.execute(
            """
            INSERT INTO subscribers
                (subscriber_id, email, tier, api_key, delivery_method, webhook_url, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(subscriber_id) DO UPDATE SET
                email=excluded.email,
                tier=excluded.tier,
                api_key=excluded.api_key,
                delivery_method=excluded.delivery_method,
                webhook_url=excluded.webhook_url,
                status=excluded.status
            """,
            (
                str(subscriber["subscriber_id"]),
                subscriber.get("email"),
                str(subscriber["tier"]),
                str(subscriber["api_key"]),
                str(subscriber["delivery_method"]),
                subscriber.get("webhook_url"),
                str(subscriber.get("status", "active")),
            ),
        )


def record_dead_letter(
    subscriber_id: str,
    delivery_method: str,
    payload: dict[str, Any],
    error: str,
    attempts: int,
) -> None:
    """Persist a permanently-failed delivery for later inspection/replay."""
    with _connect() as connection:
        _ensure_schema(connection)
        connection.execute(
            """
            INSERT INTO delivery_dead_letters
                (subscriber_id, delivery_method, payload, error, attempts)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(subscriber_id),
                str(delivery_method),
                json.dumps(payload),
                str(error),
                int(attempts),
            ),
        )


def list_dead_letters(limit: int = 100) -> list[dict[str, Any]]:
    """Return the most recent dead-lettered deliveries, newest first."""
    with _connect() as connection:
        _ensure_schema(connection)
        rows = connection.execute(
            """
            SELECT id, subscriber_id, delivery_method, payload, error, attempts, created_at
            FROM delivery_dead_letters
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
    results = []
    for row in rows:
        item = dict(row)
        item["payload"] = json.loads(item["payload"])
        results.append(item)
    return results
