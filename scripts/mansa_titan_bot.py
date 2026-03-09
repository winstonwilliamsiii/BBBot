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

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd
import requests
from dotenv import load_dotenv

from scripts.load_screener_csv import load_bot_trade_candidates

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
    profile = _default_bot_profile()

    if not config_path:
        return profile

    if yaml is None:
        logger.warning("PyYAML not installed; using default bot profile")
        return profile

    path = Path(config_path)
    if not path.exists():
        logger.info("Bot config file not found at %s; using defaults", path)
        return profile

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except (OSError, ValueError, TypeError) as exc:
        logger.warning("Failed reading bot config %s: %s", path, exc)
        return profile

    if not isinstance(data, dict):
        return profile

    bots = data.get("bots", {})
    if not isinstance(bots, dict) or not bots:
        return profile

    active_bot = requested_bot or data.get("active_bot") or "Titan_Bot"
    if active_bot not in bots:
        logger.warning(
            "Active bot '%s' not found in config; falling back to default profile",
            active_bot,
        )
        return profile

    bot_profile = bots.get(active_bot) or {}
    if not isinstance(bot_profile, dict):
        return profile

    merged = {
        **profile,
        **bot_profile,
        "bot_name": active_bot,
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
    dry_run: bool
    enable_trading: bool
    strategy_name: str
    active_bot_name: str = "Titan_Bot"
    screener_file: str = "titan_tech_fundamentals.csv"
    universe: str = "Mag7+Tech"
    position_size: float = 5000.0
    risk_rules: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "TitanConfig":
        load_dotenv(override=False)
        bot_config_path = os.getenv(
            "BOT_CONFIG_PATH",
            "config/fundamentals_bots.yml",
        )
        requested_bot = os.getenv("ACTIVE_BOT") or os.getenv("BOT_NAME")
        bot_profile = _load_active_bot_profile(bot_config_path, requested_bot)

        return cls(
            alpaca_api_key=os.getenv("ALPACA_API_KEY"),
            alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY"),
            alpaca_base_url=os.getenv(
                "ALPACA_BASE_URL",
                "https://paper-api.alpaca.markets",
            ),
            discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
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
            dry_run=_as_bool(os.getenv("TITAN_DRY_RUN", "true"), True),
            enable_trading=_as_bool(
                os.getenv("TITAN_ENABLE_TRADING", "false"),
                False,
            ),
            strategy_name=os.getenv(
                "TITAN_STRATEGY_NAME",
                str(bot_profile.get("strategy_label", "Mansa Tech - Titan Bot")),
            ),
            active_bot_name=str(bot_profile.get("bot_name", "Titan_Bot")),
            screener_file=str(
                bot_profile.get("screener_file", "titan_tech_fundamentals.csv")
            ),
            universe=str(bot_profile.get("universe", "Mag7+Tech")),
            position_size=_as_float(
                str(bot_profile.get("position_size", "5000")),
                5000.0,
            ),
            risk_rules=(
                bot_profile.get("risk_rules", {})
                if isinstance(bot_profile.get("risk_rules", {}), dict)
                else {}
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
            requests.post(
                self.config.discord_webhook_url,
                json={"content": message},
                timeout=8,
            )
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

    def load_model(self):
        if mlflow is None:
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

        order = self.api.submit_order(
            symbol=symbol,
            qty=effective_qty,
            side=side,
            type="market",
            time_in_force="day",
        )

        self.log_trade(
            symbol,
            side,
            effective_qty,
            "MARKET",
            "submitted",
            order_id=getattr(order, "id", None),
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
