from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import Engine
    from sqlalchemy.exc import SQLAlchemyError

    SQLALCHEMY_AVAILABLE = True
except Exception:
    create_engine = None
    text = None
    Engine = Any
    SQLAlchemyError = Exception
    SQLALCHEMY_AVAILABLE = False

try:
    from frontend.utils.secrets_helper import get_mysql_url
except Exception:
    get_mysql_url = None


logger = logging.getLogger(__name__)


HYDRA_STRATEGY = "hydra_momentum"


@dataclass
class PersistenceResult:
    persisted: bool
    detail: str
    analysis_id: Optional[int] = None
    trade_id: Optional[int] = None
    signal_id: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "persisted": self.persisted,
            "detail": self.detail,
            "analysis_id": self.analysis_id,
            "trade_id": self.trade_id,
            "signal_id": self.signal_id,
        }


def _database_url() -> str:
    return _candidate_database_urls()[0]


def _compose_database_url(
    host: str,
    port: str | int,
    user: str,
    password: str,
    database: str,
) -> str:
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


def _candidate_database_urls() -> list[str]:
    candidates: list[str] = []

    explicit_url = os.getenv("HYDRA_DATABASE_URL") or os.getenv(
        "HYDRA_PERSISTENCE_DATABASE_URL"
    )
    if explicit_url:
        candidates.append(explicit_url)

    has_explicit_mysql_env = any(
        os.getenv(name)
        for name in (
            "MYSQL_HOST",
            "MYSQL_PORT",
            "MYSQL_USER",
            "MYSQL_PASSWORD",
            "MYSQL_DATABASE",
            "DB_HOST",
            "DB_PORT",
            "DB_USER",
            "DB_PASSWORD",
            "DB_NAME",
        )
    )
    if has_explicit_mysql_env:
        candidates.append(
            _compose_database_url(
                os.getenv("MYSQL_HOST") or os.getenv("DB_HOST") or "127.0.0.1",
                os.getenv("MYSQL_PORT") or os.getenv("DB_PORT") or "3307",
                os.getenv("MYSQL_USER") or os.getenv("DB_USER") or "root",
                os.getenv("MYSQL_PASSWORD")
                or os.getenv("DB_PASSWORD")
                or "root",
                os.getenv("MYSQL_DATABASE")
                or os.getenv("DB_NAME")
                or "mansa_quant",
            )
        )

    # Local Docker-backed default for the FastAPI control center.
    candidates.append(
        _compose_database_url(
            "127.0.0.1",
            "3307",
            "root",
            "root",
            "mansa_quant",
        )
    )

    if get_mysql_url is not None:
        try:
            candidates.append(get_mysql_url())
        except Exception:
            pass

    deduped: list[str] = []
    for candidate in candidates:
        if candidate and candidate not in deduped:
            deduped.append(candidate)
    return deduped


def _get_engine() -> Engine:
    if not SQLALCHEMY_AVAILABLE or create_engine is None:
        raise RuntimeError("sqlalchemy is not installed")

    last_error: Optional[Exception] = None
    for database_url in _candidate_database_urls():
        try:
            engine = create_engine(database_url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return engine
        except SQLAlchemyError as exc:
            last_error = exc

    raise RuntimeError(
        "Unable to connect to any Hydra persistence database target"
        + (f": {last_error}" if last_error else "")
    )


def ensure_hydra_tables(engine: Optional[Engine] = None) -> None:
    active_engine = engine or _get_engine()
    ddl = [
        """
        CREATE TABLE IF NOT EXISTS trading_signals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ticker VARCHAR(10) NOT NULL,
            `signal` INT NOT NULL,
            price FLOAT NOT NULL,
            `timestamp` DATETIME NOT NULL,
            strategy VARCHAR(50) NOT NULL,
            INDEX idx_ticker (ticker),
            INDEX idx_timestamp (timestamp),
            INDEX idx_strategy (strategy)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS trades_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ticker VARCHAR(10) NOT NULL,
            `action` VARCHAR(10) NOT NULL,
            shares INT NOT NULL,
            price FLOAT NOT NULL,
            `value` FLOAT NOT NULL,
            `timestamp` DATETIME NOT NULL,
            `status` VARCHAR(20) NOT NULL,
            order_id VARCHAR(50),
            strategy VARCHAR(50) NOT NULL,
            INDEX idx_ticker (ticker),
            INDEX idx_timestamp (timestamp),
            INDEX idx_status (status),
            INDEX idx_strategy (strategy)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS hydra_analysis_runs (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            ticker VARCHAR(16) NOT NULL,
            action VARCHAR(16) NOT NULL,
            composite_score DECIMAL(12, 6) NOT NULL,
            momentum_score DECIMAL(12, 6) NOT NULL,
            fundamental_score DECIMAL(12, 6) NOT NULL,
            technical_score DECIMAL(12, 6) NOT NULL,
            sentiment_score DECIMAL(12, 6) NOT NULL,
            latest_price DECIMAL(18, 6) NULL,
            headline_count INT NOT NULL DEFAULT 0,
            airflow_dag_id VARCHAR(128) NULL,
            payload_json JSON NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_hydra_analysis_ticker (ticker),
            INDEX idx_hydra_analysis_action (action),
            INDEX idx_hydra_analysis_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        """
        CREATE TABLE IF NOT EXISTS hydra_trade_decisions (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            analysis_id BIGINT NULL,
            broker VARCHAR(32) NOT NULL,
            ticker VARCHAR(16) NOT NULL,
            action VARCHAR(16) NOT NULL,
            qty DECIMAL(18, 6) NOT NULL,
            price DECIMAL(18, 6) NULL,
            value DECIMAL(18, 6) NULL,
            dry_run BOOLEAN NOT NULL DEFAULT TRUE,
            status VARCHAR(32) NOT NULL,
            order_id VARCHAR(100) NULL,
            payload_json JSON NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_hydra_trade_ticker (ticker),
            INDEX idx_hydra_trade_status (status),
            INDEX idx_hydra_trade_created_at (created_at),
            CONSTRAINT fk_hydra_trade_analysis
                FOREIGN KEY (analysis_id) REFERENCES hydra_analysis_runs(id)
                ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
    ]

    with active_engine.begin() as conn:
        for statement in ddl:
            conn.execute(text(statement))


def _signal_value(action: str) -> int:
    normalized = str(action or "").strip().upper()
    if normalized == "BUY":
        return 1
    if normalized == "SELL":
        return -1
    return 0


def persist_hydra_analysis(
    analysis: dict[str, Any],
    *,
    airflow_dag_id: Optional[str] = None,
) -> dict[str, Any]:
    try:
        engine = _get_engine()
        ensure_hydra_tables(engine)
        payload_json = json.dumps(analysis, default=str)
        latest_price = analysis.get("latest_price")
        signal_value = _signal_value(analysis.get("action", "HOLD"))

        with engine.begin() as conn:
            result = conn.execute(
                text(
                    """
                    INSERT INTO hydra_analysis_runs (
                        ticker,
                        action,
                        composite_score,
                        momentum_score,
                        fundamental_score,
                        technical_score,
                        sentiment_score,
                        latest_price,
                        headline_count,
                        airflow_dag_id,
                        payload_json
                    ) VALUES (
                        :ticker,
                        :action,
                        :composite_score,
                        :momentum_score,
                        :fundamental_score,
                        :technical_score,
                        :sentiment_score,
                        :latest_price,
                        :headline_count,
                        :airflow_dag_id,
                        CAST(:payload_json AS JSON)
                    )
                    """
                ),
                {
                    "ticker": analysis.get("ticker"),
                    "action": analysis.get("action", "HOLD"),
                    "composite_score": float(
                        analysis.get("composite_score", 0.0)
                    ),
                    "momentum_score": float(
                        analysis.get("momentum", {}).get("score", 0.0)
                    ),
                    "fundamental_score": float(
                        analysis.get("fundamental", {}).get("score", 0.0)
                    ),
                    "technical_score": float(
                        analysis.get("technical", {}).get("score", 0.0)
                    ),
                    "sentiment_score": float(
                        analysis.get("sentiment", {}).get("score", 0.0)
                    ),
                    "latest_price": latest_price,
                    "headline_count": int(
                        analysis.get("sentiment", {}).get("headline_count", 0)
                    ),
                    "airflow_dag_id": airflow_dag_id,
                    "payload_json": payload_json,
                },
            )
            analysis_id = int(result.lastrowid or 0) or None

            signal_result = conn.execute(
                text(
                    """
                    INSERT INTO trading_signals (
                        ticker,
                        `signal`,
                        price,
                        `timestamp`,
                        strategy
                    ) VALUES (
                        :ticker,
                        :signal,
                        :price,
                        :timestamp,
                        :strategy
                    )
                    """
                ),
                {
                    "ticker": analysis.get("ticker"),
                    "signal": signal_value,
                    "price": float(latest_price or 0.0),
                    "timestamp": datetime.utcnow(),
                    "strategy": HYDRA_STRATEGY,
                },
            )
            signal_id = int(signal_result.lastrowid or 0) or None

        return PersistenceResult(
            persisted=True,
            detail="Hydra analysis persisted to MySQL",
            analysis_id=analysis_id,
            signal_id=signal_id,
        ).to_dict()
    except Exception as exc:
        logger.warning("Hydra analysis persistence skipped: %s", exc)
        return PersistenceResult(
            persisted=False,
            detail=str(exc),
        ).to_dict()


def persist_hydra_trade_decision(
    trade_result: dict[str, Any],
    *,
    analysis: Optional[dict[str, Any]] = None,
    analysis_id: Optional[int] = None,
) -> dict[str, Any]:
    try:
        engine = _get_engine()
        ensure_hydra_tables(engine)
        ticker = str(trade_result.get("ticker", "")).strip().upper()
        qty = float(trade_result.get("qty", 0.0) or 0.0)
        price = None
        if analysis is not None:
            price = analysis.get("latest_price")
        if price is None:
            price = trade_result.get("price")

        numeric_price = float(price) if price not in (None, "") else 0.0
        value = round(qty * numeric_price, 6) if numeric_price else 0.0
        payload_json = json.dumps(trade_result, default=str)
        status = str(trade_result.get("status", "unknown")).strip().upper()

        with engine.begin() as conn:
            result = conn.execute(
                text(
                    """
                    INSERT INTO hydra_trade_decisions (
                        analysis_id,
                        broker,
                        ticker,
                        action,
                        qty,
                        price,
                        value,
                        dry_run,
                        status,
                        order_id,
                        payload_json
                    ) VALUES (
                        :analysis_id,
                        :broker,
                        :ticker,
                        :action,
                        :qty,
                        :price,
                        :value,
                        :dry_run,
                        :status,
                        :order_id,
                        CAST(:payload_json AS JSON)
                    )
                    """
                ),
                {
                    "analysis_id": analysis_id,
                    "broker": trade_result.get("broker", "unknown"),
                    "ticker": ticker,
                    "action": trade_result.get("action", "HOLD"),
                    "qty": qty,
                    "price": numeric_price if numeric_price else None,
                    "value": value if value else None,
                    "dry_run": bool(trade_result.get("dry_run", True)),
                    "status": status,
                    "order_id": trade_result.get("order_id"),
                    "payload_json": payload_json,
                },
            )
            trade_id = int(result.lastrowid or 0) or None

            trades_result = conn.execute(
                text(
                    """
                    INSERT INTO trades_history (
                        ticker,
                        `action`,
                        shares,
                        price,
                        `value`,
                        `timestamp`,
                        `status`,
                        order_id,
                        strategy
                    ) VALUES (
                        :ticker,
                        :action,
                        :shares,
                        :price,
                        :value,
                        :timestamp,
                        :status,
                        :order_id,
                        :strategy
                    )
                    """
                ),
                {
                    "ticker": ticker,
                    "action": trade_result.get("action", "HOLD"),
                    "shares": int(qty),
                    "price": numeric_price,
                    "value": value,
                    "timestamp": datetime.utcnow(),
                    "status": status,
                    "order_id": trade_result.get("order_id") or None,
                    "strategy": HYDRA_STRATEGY,
                },
            )

        return PersistenceResult(
            persisted=True,
            detail="Hydra trade persisted to MySQL",
            analysis_id=analysis_id,
            trade_id=trade_id,
            signal_id=int(trades_result.lastrowid or 0) or None,
        ).to_dict()
    except Exception as exc:
        logger.warning("Hydra trade persistence skipped: %s", exc)
        return PersistenceResult(
            persisted=False,
            detail=str(exc),
            analysis_id=analysis_id,
        ).to_dict()
