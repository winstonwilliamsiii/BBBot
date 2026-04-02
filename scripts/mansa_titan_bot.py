"""
Mansa Tech - Titan Bot

Project-aligned trading bot module with:
- Alpaca execution support
- MySQL persistence for trade/activity logs
- MLflow prediction integration
- Airflow/Airbyte/MLflow health checks
- Streamlit dashboard data helpers
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd
import requests
from dotenv import load_dotenv

try:
    from scripts.load_screener_csv import load_bot_trade_candidates
    from scripts.load_screener_csv import (
        DEFAULT_CONFIG_PATH,
        load_bot_config as load_runtime_bot_config,
    )
except ModuleNotFoundError:
    from load_screener_csv import load_bot_trade_candidates
    from load_screener_csv import (
        DEFAULT_CONFIG_PATH,
        load_bot_config as load_runtime_bot_config,
    )

try:
    import yaml
except ImportError:
    yaml = None

try:
    import alpaca_trade_api as tradeapi
except ImportError:
    tradeapi = None

try:
    import mlflow
    from mlflow.exceptions import MlflowException
except ImportError:
    mlflow = None
    MlflowException = RuntimeError

try:
    import mysql.connector
except ImportError:
    mysql = None


logger = logging.getLogger(__name__)


def _default_bot_profile(bot_name: str = "Titan_Bot") -> Dict[str, Any]:
    return {
        "bot_name": bot_name,
        "screener_file": "titan_tech_fundamentals.csv",
        "universe": "Mag7+Tech",
        "position_size": 5000.0,
        "strategy_label": "Tech_Fundamentals_Mag7",
        "risk_rules": {
            "min_volume": 5000000,
            "max_pe": 40,
            "min_roe": 15,
            "max_debt_to_equity": 0.8,
        },
    }


def _load_active_bot_profile(
    config_path: Optional[str],
    requested_bot: Optional[str],
) -> Dict[str, Any]:
    active_name = requested_bot or ""
    if not active_name and config_path and os.path.isdir(config_path):
        active_name = "Titan"

    default_profile_name = active_name or "Titan_Bot"
    if default_profile_name and not default_profile_name.endswith("_Bot"):
        default_profile_name = f"{default_profile_name}_Bot"

    profile = _default_bot_profile(default_profile_name)

    if not config_path:
        return profile

    try:
        bot_profile = load_runtime_bot_config(active_name, config_path=config_path)
    except (OSError, ValueError, TypeError, FileNotFoundError) as exc:
        logger.warning("Failed reading bot config %s: %s", config_path, exc)
        return profile

    merged = {
        **profile,
        **bot_profile,
        "bot_name": str(bot_profile.get("bot_name") or active_name),
    }

    if "risk_rules" not in merged or not isinstance(merged["risk_rules"], dict):
        merged["risk_rules"] = profile["risk_rules"]

    return merged


def _as_bool(value: str, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _as_int(value: Optional[str], default: int) -> int:
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _as_float(value: Optional[str], default: float) -> float:
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


@dataclass
class TitanConfig:
    alpaca_api_key: Optional[str]
    alpaca_secret_key: Optional[str]
    alpaca_base_url: str
    discord_webhook_url: Optional[str]
    mysql_host: str
    mysql_port: int
    mysql_user: str
    mysql_password: str
    mysql_database: str
    titan_trades_table: str
    titan_service_table: str
    mlflow_tracking_uri: str
    titan_model_uri: str
    airflow_base_url: str
    airbyte_base_url: str
    airbyte_connection_id: Optional[str]
    liquidity_buffer_threshold: float
    prediction_threshold: float
    order_timeout_seconds: float
    dry_run: bool
    enable_trading: bool
    strategy_name: str
    active_bot_name: str = "Titan_Bot"
    screener_file: str = "titan_tech_fundamentals.csv"
    universe: str = "Mag7+Tech"
    position_size: float = 5000.0
    risk_rules: Dict[str, Any] = field(default_factory=dict)
    selection_mode: str = "technical"
    manual_symbols: List[str] = field(default_factory=list)
    technical_lookback_days: int = 120

    @classmethod
    def from_env(cls) -> "TitanConfig":
        requested_bot = os.getenv("ACTIVE_BOT") or os.getenv("BOT_NAME")
        load_dotenv(override=False)
        bot_config_path = os.getenv(
            "BOT_CONFIG_PATH",
            str(DEFAULT_CONFIG_PATH),
        )
        bot_profile = _load_active_bot_profile(bot_config_path, requested_bot)

        return cls(
            alpaca_api_key=os.getenv("ALPACA_API_KEY"),
            alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY"),
            alpaca_base_url=os.getenv(
                "ALPACA_BASE_URL",
                "https://paper-api.alpaca.markets",
            ),
            discord_webhook_url=(
                os.getenv("DISCORD_WEBHOOK_URL")
                or os.getenv("DISCORD_WEBHOOK")
                or os.getenv("DISCORD_WEBHOOK_PROD")
            ),
            mysql_host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            mysql_port=_as_int(os.getenv("MYSQL_PORT"), 3307),
            mysql_user=os.getenv("MYSQL_USER", "root"),
            mysql_password=os.getenv("MYSQL_PASSWORD", "root"),
            mysql_database=os.getenv("MYSQL_DATABASE", "mansa_bot"),
            titan_trades_table=os.getenv("TITAN_TRADES_TABLE", "titan_trades"),
            titan_service_table=os.getenv(
                "TITAN_SERVICE_HEALTH_TABLE",
                "titan_service_health",
            ),
            mlflow_tracking_uri=os.getenv(
                "MLFLOW_TRACKING_URI",
                "http://localhost:5000",
            ),
            titan_model_uri=os.getenv(
                "TITAN_MODEL_URI",
                "models:/TitanRiskModel/Production",
            ),
            airflow_base_url=os.getenv(
                "AIRFLOW_BASE_URL",
                "http://localhost:8080",
            ),
            airbyte_base_url=os.getenv(
                "AIRBYTE_BASE_URL",
                "http://localhost:8001",
            ),
            airbyte_connection_id=os.getenv("AIRBYTE_CONNECTION_ID"),
            liquidity_buffer_threshold=_as_float(
                os.getenv("TITAN_LIQUIDITY_BUFFER"),
                0.20,
            ),
            prediction_threshold=_as_float(
                os.getenv("TITAN_PREDICTION_THRESHOLD"),
                0.50,
            ),
            order_timeout_seconds=_as_float(
                os.getenv("TITAN_ORDER_TIMEOUT_SECONDS"),
                15.0,
            ),
            dry_run=_as_bool(os.getenv("TITAN_DRY_RUN", "true"), True),
            enable_trading=_as_bool(
                os.getenv("TITAN_ENABLE_TRADING", "false"),
                False,
            ),
            strategy_name=os.getenv(
                "TITAN_STRATEGY_NAME",
                str(
                    bot_profile.get(
                        "strategy_label",
                        bot_profile.get("strategy_name", "Mansa Tech - Titan Bot"),
                    )
                ),
            ),
            active_bot_name=str(bot_profile.get("bot_name", "Titan_Bot")),
            screener_file=str(
                bot_profile.get("screener_file") or "titan_tech_fundamentals.csv"
            ),
            universe=str(bot_profile.get("universe") or "Mag7+Tech"),
            position_size=_as_float(
                str(bot_profile.get("position_size") or "5000"),
                5000.0,
            ),
            risk_rules=(
                bot_profile.get("risk_rules", {})
                if isinstance(bot_profile.get("risk_rules", {}), dict)
                else {}
            ),
            selection_mode=str(
                os.getenv("TITAN_SELECTION_MODE", "technical")
            ).strip().lower(),
            manual_symbols=[
                s.strip().upper()
                for s in str(os.getenv("TITAN_MANUAL_SYMBOLS", "")).split(",")
                if s.strip()
            ],
            technical_lookback_days=max(
                30,
                _as_int(os.getenv("TITAN_TECH_LOOKBACK_DAYS"), 120),
            ),
        )

    def mysql_config(self) -> Dict[str, Any]:
        return {
            "host": self.mysql_host,
            "port": self.mysql_port,
            "user": self.mysql_user,
            "password": self.mysql_password,
            "database": self.mysql_database,
        }


class TitanBot:
    def __init__(self, config: Optional[TitanConfig] = None):
        self.config = config or TitanConfig.from_env()
        self.api = self._init_alpaca_client()

    def _alpaca_headers(self) -> Dict[str, str]:
        return {
            "APCA-API-KEY-ID": self.config.alpaca_api_key or "",
            "APCA-API-SECRET-KEY": self.config.alpaca_secret_key or "",
            "Content-Type": "application/json",
        }

    def _extract_order_id(self, order: Any) -> Optional[str]:
        if isinstance(order, dict):
            order_id = order.get("id")
            return str(order_id) if order_id else None

        order_id = getattr(order, "id", None)
        return str(order_id) if order_id else None

    def _submit_alpaca_order(
        self,
        symbol: str,
        qty: float,
        side: str,
    ) -> Dict[str, Any]:
        if not self.config.alpaca_api_key or not self.config.alpaca_secret_key:
            raise RuntimeError("Alpaca credentials missing")

        endpoint = f"{self.config.alpaca_base_url.rstrip('/')}/v2/orders"
        payload = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": "market",
            "time_in_force": "day",
        }

        logger.info(
            "Submitting Alpaca order for %s %s qty=%s with timeout=%ss",
            side,
            symbol,
            qty,
            self.config.order_timeout_seconds,
        )

        env = os.environ.copy()
        env["TITAN_SUBMIT_ENDPOINT"] = endpoint
        env["TITAN_SUBMIT_PAYLOAD"] = json.dumps(payload)
        env["TITAN_SUBMIT_HEADERS"] = json.dumps(self._alpaca_headers())
        env["TITAN_ORDER_TIMEOUT_SECONDS"] = str(
            self.config.order_timeout_seconds
        )

        submit_script = (
            "import json, os, requests;"
            "endpoint=os.environ['TITAN_SUBMIT_ENDPOINT'];"
            "payload=json.loads(os.environ['TITAN_SUBMIT_PAYLOAD']);"
            "headers=json.loads(os.environ['TITAN_SUBMIT_HEADERS']);"
            "timeout=float(os.environ['TITAN_ORDER_TIMEOUT_SECONDS']);"
            "resp=requests.post(endpoint, headers=headers, json=payload, timeout=timeout);"
            "resp.raise_for_status();"
            "print(json.dumps(resp.json()))"
        )

        try:
            completed = subprocess.run(
                [sys.executable, "-c", submit_script],
                capture_output=True,
                text=True,
                env=env,
                timeout=self.config.order_timeout_seconds + 3.0,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise requests.Timeout(
                f"Timed out submitting Alpaca order after {self.config.order_timeout_seconds}s"
            ) from exc

        if completed.returncode != 0:
            stderr = (completed.stderr or completed.stdout or "").strip()
            raise requests.RequestException(
                stderr or "Unknown Alpaca order submission failure"
            )

        return json.loads(completed.stdout.strip())

    def _mlflow_tracking_is_reachable(self) -> bool:
        if mlflow is None:
            return False

        health_url = f"{self.config.mlflow_tracking_uri.rstrip('/')}/health"
        try:
            response = requests.get(health_url, timeout=2)
            return 200 <= response.status_code < 300
        except requests.RequestException:
            logger.info(
                "Skipping MLflow model load because tracking URI is unavailable: %s",
                health_url,
            )
            return False

    def _init_alpaca_client(self):
        if tradeapi is None:
            logger.warning(
                "alpaca_trade_api not installed; trade execution disabled"
            )
            return None
        if not self.config.alpaca_api_key or not self.config.alpaca_secret_key:
            logger.warning(
                "Alpaca credentials missing; trade execution disabled"
            )
            return None

        return tradeapi.REST(
            self.config.alpaca_api_key,
            self.config.alpaca_secret_key,
            self.config.alpaca_base_url,
        )

    def ensure_database_tables(self) -> None:
        if mysql is None:
            raise RuntimeError("mysql-connector-python is not installed")

        conn = mysql.connector.connect(**self.config.mysql_config())
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.config.titan_trades_table} (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    qty DECIMAL(18, 6) NOT NULL,
                    price_source VARCHAR(40),
                    status VARCHAR(20) NOT NULL,
                    order_id VARCHAR(80),
                    prediction_label INT,
                    prediction_probability DECIMAL(10, 6),
                    strategy VARCHAR(100),
                    notes VARCHAR(255),
                    INDEX idx_titan_timestamp (timestamp),
                    INDEX idx_titan_symbol (symbol),
                    INDEX idx_titan_status (status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.config.titan_service_table} (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME NOT NULL,
                    service_name VARCHAR(40) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    endpoint VARCHAR(255),
                    detail TEXT,
                    INDEX idx_service_time (timestamp),
                    INDEX idx_service_name (service_name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _notify_discord(self, message: str) -> None:
        if not self.config.discord_webhook_url:
            return
        try:
            response = requests.post(
                self.config.discord_webhook_url,
                json={"content": message},
                timeout=8,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Discord notification failed: %s", exc)

    def get_account_snapshot(self) -> Dict[str, float]:
        if self.api is None:
            return {"cash": 0.0, "equity": 0.0}

        account = self.api.get_account()
        return {
            "cash": float(account.cash),
            "equity": float(account.equity),
        }

    def titan_guard(self, buffer_threshold: Optional[float] = None) -> bool:
        if buffer_threshold is None:
            threshold = self.config.liquidity_buffer_threshold
        else:
            threshold = buffer_threshold
        snapshot = self.get_account_snapshot()
        equity = snapshot.get("equity", 0.0)
        cash = snapshot.get("cash", 0.0)

        if equity <= 0:
            return False

        ratio = cash / equity
        if ratio < threshold:
            message = (
                "Titan blocked trade: liquidity buffer breached "
                f"({ratio:.2%} < {threshold:.2%})."
            )
            logger.warning(message)
            self._notify_discord(message)
            return False
        return True

    def _passes_configured_risk_rules(
        self,
        fundamentals: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        rules = self.config.risk_rules or {}
        if not rules:
            return True, "no-risk-rules"

        fundamentals_data = fundamentals or {}
        if not fundamentals_data:
            return True, "no-fundamentals-provided"

        min_volume = rules.get("min_volume")
        if min_volume is not None:
            volume = fundamentals_data.get("volume")
            if volume is not None and float(volume) < float(min_volume):
                return False, "min_volume"

        max_pe = rules.get("max_pe")
        if max_pe is not None:
            pe_ratio = fundamentals_data.get("pe")
            if pe_ratio is not None and float(pe_ratio) > float(max_pe):
                return False, "max_pe"

        min_roe = rules.get("min_roe")
        if min_roe is not None:
            roe = fundamentals_data.get("roe")
            if roe is not None and float(roe) < float(min_roe):
                return False, "min_roe"

        max_debt_to_equity = rules.get("max_debt_to_equity")
        if max_debt_to_equity is not None:
            debt_to_equity = fundamentals_data.get("debt_to_equity")
            if (
                debt_to_equity is not None
                and float(debt_to_equity) > float(max_debt_to_equity)
            ):
                return False, "max_debt_to_equity"

        min_dividend_yield = rules.get("min_dividend_yield")
        if min_dividend_yield is not None:
            dividend_yield = fundamentals_data.get("dividend_yield")
            if (
                dividend_yield is not None
                and float(dividend_yield) < float(min_dividend_yield)
            ):
                return False, "min_dividend_yield"

        return True, "passed"

    def _effective_order_qty(self, qty: Optional[float]) -> float:
        if qty is None or qty <= 0:
            return float(self.config.position_size)
        return float(qty)

    def _compute_rsi(self, close: pd.Series, period: int = 14) -> Optional[float]:
        if close.empty or len(close) <= period:
            return None
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(window=period).mean()
        loss = (-delta.clip(upper=0)).rolling(window=period).mean()
        rs = gain / loss.replace(0, pd.NA)
        rsi = 100 - (100 / (1 + rs))
        value = rsi.iloc[-1]
        return None if pd.isna(value) else float(value)

    def _fetch_technical_metrics(self, symbol: str) -> Dict[str, float]:
        if self.api is None:
            return {}

        try:
            bars = self.api.get_bars(
                symbol,
                "1Day",
                limit=self.config.technical_lookback_days,
                adjustment="raw",
            ).df
        except Exception as exc:
            logger.warning("Failed loading bars for %s: %s", symbol, exc)
            return {}

        if bars is None or bars.empty or "close" not in bars.columns:
            return {}

        if isinstance(bars.index, pd.MultiIndex):
            try:
                bars = bars.xs(symbol, level=0)
            except (KeyError, TypeError, ValueError):
                return {}

        close = pd.to_numeric(bars["close"], errors="coerce").dropna()
        if close.empty or len(close) < 35:
            return {}

        ema_fast = close.ewm(span=12, adjust=False).mean()
        ema_slow = close.ewm(span=26, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=9, adjust=False).mean()

        rsi = self._compute_rsi(close, period=14)
        if rsi is None:
            return {}

        macd = float(macd_line.iloc[-1])
        signal = float(signal_line.iloc[-1])
        return {
            "rsi": float(rsi),
            "macd": macd,
            "macd_signal": signal,
            "macd_hist": macd - signal,
        }

    def _score_technical_metrics(self, metrics: Dict[str, float]) -> float:
        if not metrics:
            return -999.0

        score = 0.0
        rsi = float(metrics.get("rsi", 50.0))
        macd = float(metrics.get("macd", 0.0))
        signal = float(metrics.get("macd_signal", 0.0))
        hist = float(metrics.get("macd_hist", 0.0))

        if macd > signal:
            score += 2.0
        else:
            score -= 1.0

        if 40.0 <= rsi <= 65.0:
            score += 1.5
        elif rsi < 35.0:
            score += 1.0
        elif rsi > 75.0:
            score -= 1.0

        if hist > 0:
            score += 0.5

        return score

    def _rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        mode = (self.config.selection_mode or "technical").strip().lower()
        if mode not in {"technical", "manual", "csv_order"}:
            mode = "technical"

        if mode == "manual" and self.config.manual_symbols:
            by_symbol = {
                str(item.get("symbol", "")).strip().upper(): item
                for item in candidates
            }
            ordered: List[Dict[str, Any]] = []
            for symbol in self.config.manual_symbols:
                candidate = by_symbol.get(symbol)
                if candidate is not None:
                    clone = dict(candidate)
                    clone["selection_reason"] = "manual"
                    ordered.append(clone)
            return ordered

        if mode == "csv_order":
            return candidates

        if self.api is None:
            logger.warning(
                "TITAN_SELECTION_MODE=technical but Alpaca client unavailable; using CSV order"
            )
            return candidates

        enriched: List[Dict[str, Any]] = []
        for candidate in candidates:
            symbol = str(candidate.get("symbol", "")).strip().upper()
            metrics = self._fetch_technical_metrics(symbol)
            score = self._score_technical_metrics(metrics)
            clone = dict(candidate)
            clone["technical_metrics"] = metrics
            clone["technical_score"] = score
            clone["selection_reason"] = "technical"
            enriched.append(clone)

        enriched.sort(
            key=lambda item: (
                float(item.get("technical_score", -999.0)),
                str(item.get("symbol", "")),
            ),
            reverse=True,
        )
        return enriched

    def load_model(self):
        if mlflow is None or not self._mlflow_tracking_is_reachable():
            return None
        try:
            mlflow.set_tracking_uri(self.config.mlflow_tracking_uri)
            return mlflow.sklearn.load_model(self.config.titan_model_uri)
        except (
            AttributeError,
            OSError,
            RuntimeError,
            ValueError,
            MlflowException,
        ) as exc:
            logger.warning("MLflow model load failed: %s", exc)
            return None

    def titan_predict(self, features: Sequence[float]) -> Tuple[int, float]:
        model = self.load_model()
        if model is None:
            return 1, 0.5

        try:
            prediction = int(model.predict([list(features)])[0])
        except (AttributeError, IndexError, TypeError, ValueError) as exc:
            logger.warning("Prediction inference failed, using fallback: %s", exc)
            return 1, 0.5

        probability = 0.5
        try:
            probability = float(model.predict_proba([list(features)])[0][1])
        except (AttributeError, IndexError, TypeError, ValueError):
            probability = 0.5

        try:
            if mlflow is not None:
                mlflow.log_metric("titan_prediction_probability", probability)
        except (RuntimeError, TypeError, ValueError):
            pass

        return prediction, probability

    def log_trade(
        self,
        symbol: str,
        side: str,
        qty: float,
        price_source: str,
        status: str,
        order_id: Optional[str] = None,
        prediction_label: Optional[int] = None,
        prediction_probability: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> None:
        if mysql is None:
            raise RuntimeError("mysql-connector-python is not installed")

        conn = mysql.connector.connect(**self.config.mysql_config())
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {self.config.titan_trades_table}
                (timestamp, symbol, side, qty, price_source, status, order_id,
                 prediction_label, prediction_probability, strategy, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    datetime.now(timezone.utc).replace(tzinfo=None),
                    symbol,
                    side,
                    qty,
                    price_source,
                    status,
                    order_id,
                    prediction_label,
                    prediction_probability,
                    self.config.strategy_name,
                    notes,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def execute_trade(
        self,
        symbol: str,
        side: str,
        qty: Optional[float],
        features: Sequence[float],
        fundamentals: Optional[Dict[str, Any]] = None,
    ):
        effective_qty = self._effective_order_qty(qty)
        prediction, probability = self.titan_predict(features)
        passes_ml_gate = (
            prediction == 1
            and probability >= self.config.prediction_threshold
        )
        passes_risk_gate = self.titan_guard()
        passes_fundamental_risk_rules, failed_risk_rule = (
            self._passes_configured_risk_rules(fundamentals)
        )

        try:
            if mlflow is not None:
                mlflow.log_param("active_bot", self.config.active_bot_name)
                mlflow.log_param("strategy_label", self.config.strategy_name)
        except (RuntimeError, TypeError, ValueError):
            pass

        if not passes_ml_gate:
            self.log_trade(
                symbol,
                side,
                effective_qty,
                "MARKET",
                "blocked",
                prediction_label=prediction,
                prediction_probability=probability,
                notes="ML gate rejected trade",
            )
            return None

        if not passes_risk_gate:
            self.log_trade(
                symbol,
                side,
                effective_qty,
                "MARKET",
                "blocked",
                prediction_label=prediction,
                prediction_probability=probability,
                notes="Liquidity guard blocked trade",
            )
            return None

        if not passes_fundamental_risk_rules:
            self.log_trade(
                symbol,
                side,
                effective_qty,
                "MARKET",
                "blocked",
                prediction_label=prediction,
                prediction_probability=probability,
                notes=(
                    "Risk rule blocked trade: "
                    f"{failed_risk_rule}"
                ),
            )
            return None

        if (
            self.config.dry_run
            or not self.config.enable_trading
            or self.api is None
        ):
            self.log_trade(
                symbol,
                side,
                effective_qty,
                "MARKET",
                "simulated",
                prediction_label=prediction,
                prediction_probability=probability,
                notes="Dry-run mode",
            )
            return None

        try:
            order = self._submit_alpaca_order(
                symbol=symbol,
                qty=effective_qty,
                side=side,
            )
        except requests.RequestException as exc:
            logger.error("Alpaca order submission failed for %s: %s", symbol, exc)
            self.log_trade(
                symbol,
                side,
                effective_qty,
                "MARKET",
                "error",
                prediction_label=prediction,
                prediction_probability=probability,
                notes=f"Alpaca submit failed: {exc}",
            )
            return None
        except RuntimeError as exc:
            logger.error("Alpaca order submission blocked for %s: %s", symbol, exc)
            self.log_trade(
                symbol,
                side,
                effective_qty,
                "MARKET",
                "error",
                prediction_label=prediction,
                prediction_probability=probability,
                notes=str(exc),
            )
            return None

        self.log_trade(
            symbol,
            side,
            effective_qty,
            "MARKET",
            "submitted",
            order_id=self._extract_order_id(order),
            prediction_label=prediction,
            prediction_probability=probability,
        )
        self._notify_discord(
            f"Titan executed {side} order for {effective_qty} {symbol}"
        )
        return order

    def execute_from_screener(
        self,
        side: str = "buy",
        max_trades: Optional[int] = None,
        features_by_symbol: Optional[Dict[str, Sequence[float]]] = None,
    ) -> List[Dict[str, Any]]:
        candidates = load_bot_trade_candidates(self.config.active_bot_name)
        candidates = self._rank_candidates(candidates)
        if max_trades is not None and max_trades > 0:
            candidates = candidates[:max_trades]

        results: List[Dict[str, Any]] = []
        for candidate in candidates:
            symbol = str(candidate.get("symbol", "")).strip().upper()
            if not symbol:
                continue

            fundamentals = candidate.get("fundamentals")
            if not isinstance(fundamentals, dict):
                fundamentals = {}

            features: Sequence[float] = []
            if features_by_symbol:
                symbol_features = features_by_symbol.get(symbol)
                if isinstance(symbol_features, Sequence):
                    features = symbol_features

            order = self.execute_trade(
                symbol=symbol,
                side=side,
                qty=None,
                features=features,
                fundamentals=fundamentals,
            )
            results.append(
                {
                    "symbol": symbol,
                    "executed": order is not None,
                    "fundamentals": fundamentals,
                    "technical_score": candidate.get("technical_score"),
                    "technical_metrics": candidate.get("technical_metrics", {}),
                    "selection_reason": candidate.get("selection_reason", "csv_order"),
                }
            )

        return results

    def _http_health(self, url: str, timeout: int = 8) -> Tuple[str, str]:
        try:
            resp = requests.get(url, timeout=timeout)
            if 200 <= resp.status_code < 300:
                return "healthy", f"HTTP {resp.status_code}"
            return "warning", f"HTTP {resp.status_code}"
        except requests.RequestException as exc:
            return "error", str(exc)

    def collect_service_health(self) -> List[Dict[str, str]]:
        mlflow_status, mlflow_detail = self._http_health(
            f"{self.config.mlflow_tracking_uri.rstrip('/')}/health"
        )
        airflow_status, airflow_detail = self._http_health(
            f"{self.config.airflow_base_url.rstrip('/')}/health"
        )

        airbyte_health_url = (
            f"{self.config.airbyte_base_url.rstrip('/')}/health"
        )
        airbyte_status, airbyte_detail = self._http_health(airbyte_health_url)
        if airbyte_status == "error":
            fallback_url = (
                f"{self.config.airbyte_base_url.rstrip('/')}/api/v1/health"
            )
            airbyte_status, airbyte_detail = self._http_health(fallback_url)
            airbyte_health_url = fallback_url

        rows = [
            {
                "service_name": "mlflow",
                "status": mlflow_status,
                "endpoint": (
                    f"{self.config.mlflow_tracking_uri.rstrip('/')}/health"
                ),
                "detail": mlflow_detail,
            },
            {
                "service_name": "airflow",
                "status": airflow_status,
                "endpoint": (
                    f"{self.config.airflow_base_url.rstrip('/')}/health"
                ),
                "detail": airflow_detail,
            },
            {
                "service_name": "airbyte",
                "status": airbyte_status,
                "endpoint": airbyte_health_url,
                "detail": airbyte_detail,
            },
        ]

        try:
            self.log_service_health(rows)
        except (OSError, RuntimeError, ValueError) as exc:
            logger.warning("Could not persist service health: %s", exc)

        return rows

    def log_service_health(self, rows: List[Dict[str, str]]) -> None:
        if mysql is None:
            raise RuntimeError("mysql-connector-python is not installed")

        try:
            conn = mysql.connector.connect(**self.config.mysql_config())
        except Exception as exc:
            logger.warning(
                "Could not connect for service health logging: %s",
                exc,
            )
            return
        try:
            cursor = conn.cursor()
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            for row in rows:
                cursor.execute(
                    f"""
                    INSERT INTO {self.config.titan_service_table}
                    (timestamp, service_name, status, endpoint, detail)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        now,
                        row["service_name"],
                        row["status"],
                        row["endpoint"],
                        row["detail"],
                    ),
                )
            conn.commit()
        except Exception as exc:
            logger.warning("Could not write service health rows: %s", exc)
        finally:
            conn.close()

    def get_recent_trades(self, limit: int = 100) -> pd.DataFrame:
        if mysql is None:
            return pd.DataFrame()

        try:
            conn = mysql.connector.connect(**self.config.mysql_config())
        except Exception as exc:
            logger.warning("Could not connect for Titan trades read: %s", exc)
            return pd.DataFrame()
        try:
            query = (
                "SELECT timestamp, symbol, side, qty, status, "
                "prediction_probability "
                f"FROM {self.config.titan_trades_table} "
                f"ORDER BY timestamp DESC LIMIT %s"
            )
            df = pd.read_sql(query, conn, params=(limit,))
            if not df.empty:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df
        except Exception as exc:
            logger.warning("Could not read Titan trades: %s", exc)
            return pd.DataFrame()
        finally:
            conn.close()

    def dashboard_snapshot(self) -> Dict[str, Any]:
        trades_df = self.get_recent_trades(limit=250)
        health_rows = self.collect_service_health()

        if trades_df.empty:
            return {
                "total_trades": 0,
                "simulated_trades": 0,
                "submitted_trades": 0,
                "blocked_trades": 0,
                "avg_prediction_probability": 0.0,
                "health": health_rows,
                "trades_df": trades_df,
            }

        return {
            "total_trades": int(len(trades_df)),
            "simulated_trades": int(
                (trades_df["status"] == "simulated").sum()
            ),
            "submitted_trades": int(
                (trades_df["status"] == "submitted").sum()
            ),
            "blocked_trades": int((trades_df["status"] == "blocked").sum()),
            "avg_prediction_probability": float(
                pd.to_numeric(
                    trades_df["prediction_probability"],
                    errors="coerce",
                )
                .fillna(0.0)
                .mean()
            ),
            "health": health_rows,
            "trades_df": trades_df,
        }


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    bot = TitanBot(TitanConfig.from_env())
    bot.ensure_database_tables()
    print("Titan bot initialized successfully.")


if __name__ == "__main__":
    main()
