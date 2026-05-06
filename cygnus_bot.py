from __future__ import annotations

import importlib
import logging
import os
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

from bbbot1_pipeline.db import get_mysql_connection
from bbbot1_pipeline.mlflow_config import get_mlflow_tracking_uri


logger = logging.getLogger("cygnus_bot")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


def _optional_import(module_name: str) -> Any:
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


mlflow = _optional_import("mlflow")
statsmodels_stattools = _optional_import("statsmodels.tsa.stattools")
ib_insync = _optional_import("ib_insync")


POSITIVE_TERMS = {
    "beat",
    "beats",
    "upgrade",
    "bullish",
    "strong",
    "outperform",
    "surge",
    "buy",
}
NEGATIVE_TERMS = {
    "miss",
    "misses",
    "downgrade",
    "bearish",
    "weak",
    "underperform",
    "drop",
    "sell",
}


@dataclass
class CygnusConfig:
    name: str = "Cygnus"
    runtime_name: str = "Cygnus_Bot"
    fund: str = "Mansa Short Fund"
    strategy: str = "Relative Value Arbitrage with Short Bias and Long Bias"
    ml_model: str = "Siamese Neural Network"
    fastapi_route_prefix: str = "/cygnus"
    mlflow_experiment: str = "Cygnus_Mansa_Short_Fund"
    mlflow_tracking_uri: str = "http://127.0.0.1:5000"
    enable_mlflow_logging: bool = True
    default_pair: tuple[str, str] = ("XLF", "KRE")
    cointegration_pvalue_max: float = 0.1
    zscore_entry_short: float = 1.5
    zscore_entry_long: float = -1.5
    min_samples: int = 60


class PairAnalysisRequest(BaseModel):
    symbol_x: str = Field(min_length=1)
    symbol_y: str = Field(min_length=1)
    close_x: list[float] = Field(min_length=20)
    close_y: list[float] = Field(min_length=20)
    headlines: list[str] = Field(default_factory=list)
    mode: Literal["paper", "live"] = "paper"


class TradeRequest(BaseModel):
    symbol: str = Field(min_length=1)
    action: Literal["BUY", "SELL"]
    qty: float = Field(gt=0)
    price: Optional[float] = Field(default=None, gt=0)
    mode: Literal["paper", "live"] = "paper"
    broker: str = "ibkr"
    dry_run: bool = True


class TrainRequest(BaseModel):
    pair_id: str = "XLF_KRE"
    window_size: int = Field(default=30, ge=10, le=252)
    epochs: int = Field(default=10, ge=1, le=500)


class CygnusBot:
    def __init__(self) -> None:
        tracking_uri = os.getenv("MLFLOW_TRACKING_URI", get_mlflow_tracking_uri()).rstrip("/")
        self.config = CygnusConfig(mlflow_tracking_uri=tracking_uri)
        self._ib = None

    def _rolling_zscore(self, spread: pd.Series, window: int = 20) -> float:
        roll_mean = spread.rolling(window).mean()
        roll_std = spread.rolling(window).std(ddof=0).replace(0, np.nan)
        z = (spread - roll_mean) / roll_std
        val = float(z.iloc[-1]) if not np.isnan(z.iloc[-1]) else 0.0
        return round(val, 4)

    def _bollinger_bandwidth(self, spread: pd.Series, window: int = 20) -> float:
        ma = spread.rolling(window).mean()
        sd = spread.rolling(window).std(ddof=0)
        upper = ma + 2 * sd
        lower = ma - 2 * sd
        denom = ma.abs().replace(0, np.nan)
        bw = (upper - lower) / denom
        val = float(bw.iloc[-1]) if not np.isnan(bw.iloc[-1]) else 0.0
        return round(val, 4)

    def _smi_and_signal(self, spread: pd.Series, window: int = 14) -> tuple[float, float]:
        low = spread.rolling(window).min()
        high = spread.rolling(window).max()
        median = (high + low) / 2
        denom = ((high - low) / 2).replace(0, np.nan)
        smi = ((spread - median) / denom) * 100
        smi = smi.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        signal = smi.ewm(span=3, adjust=False).mean()
        return round(float(smi.iloc[-1]), 4), round(float(signal.iloc[-1]), 4)

    def _rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff().fillna(0.0)
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean().replace(0, np.nan)
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50.0)

    def _rsi_divergence_score(self, spread: pd.Series) -> float:
        if len(spread) < 20:
            return 0.0
        rsi = self._rsi(spread)
        price_change = float(spread.iloc[-1] - spread.iloc[-6])
        rsi_change = float(rsi.iloc[-1] - rsi.iloc[-6])
        divergence = -1.0 if np.sign(price_change) == np.sign(rsi_change) else 1.0
        strength = min(abs(price_change) / (abs(float(spread.iloc[-6])) + 1e-6), 1.0)
        return round(float(divergence * strength), 4)

    def _engle_granger_pvalue(self, x: pd.Series, y: pd.Series) -> Optional[float]:
        if statsmodels_stattools is None:
            return None
        if len(x) < 30 or len(y) < 30:
            return None
        try:
            _, pvalue, _ = statsmodels_stattools.coint(x, y)
            return round(float(pvalue), 6)
        except Exception as exc:
            logger.warning("Cointegration test failed: %s", exc)
            return None

    def _nlp_sentiment_score(self, headlines: list[str]) -> float:
        cleaned = [str(h).strip() for h in headlines if str(h).strip()]
        if not cleaned:
            return 0.0

        scores: list[float] = []
        for line in cleaned:
            tokens = {
                t.strip(" ,.!?;:-_()[]{}\"").lower()
                for t in line.split()
                if t
            }
            pos = len(tokens & POSITIVE_TERMS)
            neg = len(tokens & NEGATIVE_TERMS)
            raw = (pos - neg) / max(len(tokens), 1)
            scores.append(max(-1.0, min(1.0, raw * 8.0)))

        return round(float(np.mean(scores)), 4)

    def _siamese_similarity_proxy(self, x: pd.Series, y: pd.Series) -> float:
        # Fallback proxy when no trained Siamese network is available.
        rx = x.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)
        ry = y.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0.0)
        if rx.std(ddof=0) == 0 or ry.std(ddof=0) == 0:
            return 0.0
        corr = float(np.corrcoef(rx, ry)[0, 1])
        return round(max(-1.0, min(1.0, corr)), 4)

    def analyze_pair(self, req: PairAnalysisRequest) -> dict[str, Any]:
        x = pd.Series(req.close_x, dtype=float)
        y = pd.Series(req.close_y, dtype=float)

        sample_count = min(len(x), len(y))
        x = x.tail(sample_count).reset_index(drop=True)
        y = y.tail(sample_count).reset_index(drop=True)

        if sample_count < self.config.min_samples:
            return {
                "status": "insufficient_data",
                "required_samples": self.config.min_samples,
                "received_samples": sample_count,
            }

        hedge_ratio = float(np.polyfit(y, x, 1)[0])
        spread = x - hedge_ratio * y

        zscore = self._rolling_zscore(spread)
        bollinger_bw = self._bollinger_bandwidth(spread)
        smi, smi_signal = self._smi_and_signal(spread)
        smi_crossover = smi - smi_signal
        rsi_divergence = self._rsi_divergence_score(spread)
        cointegration_pvalue = self._engle_granger_pvalue(x, y)
        nlp_score = self._nlp_sentiment_score(req.headlines)
        siamese_similarity = self._siamese_similarity_proxy(x, y)

        coint_gate = 1.0
        if cointegration_pvalue is not None:
            coint_gate = 1.0 if cointegration_pvalue <= self.config.cointegration_pvalue_max else -0.5

        composite_score = (
            (zscore / 3.0) * 0.30
            + (smi_crossover / 100.0) * 0.20
            + rsi_divergence * 0.15
            + siamese_similarity * 0.20
            + nlp_score * 0.10
            + coint_gate * 0.05
        )
        composite_score = round(float(max(-1.0, min(1.0, composite_score))), 4)

        if zscore >= self.config.zscore_entry_short and composite_score > 0.15:
            action = "SELL"
            bias = "short_bias"
        elif zscore <= self.config.zscore_entry_long and composite_score < -0.15:
            action = "BUY"
            bias = "long_bias"
        else:
            action = "HOLD"
            bias = "neutral"

        result = {
            "status": "ok",
            "bot": self.config.name,
            "fund": self.config.fund,
            "strategy": self.config.strategy,
            "symbols": {"x": req.symbol_x.upper(), "y": req.symbol_y.upper()},
            "sample_count": sample_count,
            "hedge_ratio": round(hedge_ratio, 6),
            "indicators": {
                "bollinger_bandwidth": bollinger_bw,
                "smi": smi,
                "smi_signal": smi_signal,
                "smi_crossover": round(float(smi_crossover), 4),
                "zscore": zscore,
                "rsi_divergence": rsi_divergence,
                "cointegration_pvalue": cointegration_pvalue,
                "nlp_sentiment": nlp_score,
                "siamese_similarity": siamese_similarity,
            },
            "signal": {
                "action": action,
                "bias": bias,
                "composite_score": composite_score,
                "mode": req.mode,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._log_mlflow_pair_analysis(result)
        return result

    def _log_mlflow_pair_analysis(self, analysis: dict[str, Any]) -> dict[str, Any]:
        if mlflow is None or not self.config.enable_mlflow_logging:
            return {"logged": False, "reason": "mlflow unavailable or disabled"}

        try:
            mlflow.set_tracking_uri(self.config.mlflow_tracking_uri)
            mlflow.set_experiment(self.config.mlflow_experiment)
            run_name = f"cygnus_{analysis['symbols']['x']}_{analysis['symbols']['y']}"
            with mlflow.start_run(run_name=run_name):
                mlflow.set_tag("bot", self.config.name)
                mlflow.set_tag("fund", self.config.fund)
                mlflow.set_tag("strategy", self.config.strategy)
                mlflow.log_param("symbol_x", analysis["symbols"]["x"])
                mlflow.log_param("symbol_y", analysis["symbols"]["y"])
                mlflow.log_param("signal_action", analysis["signal"]["action"])
                for key, value in analysis["indicators"].items():
                    if value is None:
                        continue
                    mlflow.log_metric(key, float(value))
                mlflow.log_metric("composite_score", float(analysis["signal"]["composite_score"]))
                run_id = mlflow.active_run().info.run_id if mlflow.active_run() else None
            return {
                "logged": True,
                "tracking_uri": self.config.mlflow_tracking_uri,
                "experiment": self.config.mlflow_experiment,
                "run_id": run_id,
            }
        except Exception as exc:
            logger.warning("MLflow logging failed: %s", exc)
            return {
                "logged": False,
                "reason": str(exc),
                "tracking_uri": self.config.mlflow_tracking_uri,
            }

    def _connect_ib(self) -> bool:
        if ib_insync is None:
            return False
        if self._ib is not None and getattr(self._ib, "isConnected", lambda: False)():
            return True
        try:
            host = os.getenv("IB_HOST", "127.0.0.1")
            port = int(os.getenv("IB_PORT", "7497"))
            client_id = int(os.getenv("IB_CLIENT_ID", "15"))
            self._ib = ib_insync.IB()
            self._ib.connect(host, port, clientId=client_id, timeout=5)
            return bool(self._ib.isConnected())
        except Exception as exc:
            logger.warning("IBKR connection failed: %s", exc)
            self._ib = None
            return False

    def check_locates(self, symbol: str) -> dict[str, Any]:
        if ib_insync is None:
            return {
                "symbol": symbol.upper(),
                "locates_available": True,
                "reason": "ib_insync unavailable, using paper fallback",
            }

        if not self._connect_ib():
            return {
                "symbol": symbol.upper(),
                "locates_available": False,
                "reason": "unable to connect to IBKR",
            }

        try:
            contract = ib_insync.Stock(symbol.upper(), "SMART", "USD")
            self._ib.qualifyContracts(contract)
            ticker = self._ib.reqMktData(contract, genericTickList="236", snapshot=True)
            self._ib.sleep(1.0)
            shortable = float(getattr(ticker, "shortableShares", 0) or 0)
            return {
                "symbol": symbol.upper(),
                "locates_available": shortable > 0,
                "shortable_shares": shortable,
            }
        except Exception as exc:
            return {
                "symbol": symbol.upper(),
                "locates_available": False,
                "reason": str(exc),
            }

    def margin_check(self, price: float, qty: float) -> dict[str, float]:
        notional = float(price) * float(qty)
        margin_required = round(notional * 1.5, 2)
        return {
            "short_notional": round(notional, 2),
            "estimated_margin_required": margin_required,
        }

    def execute_trade(self, req: TradeRequest) -> dict[str, Any]:
        symbol = req.symbol.upper()
        status = "dry_run" if req.dry_run else "submitted"
        order_id = f"cygnus-{int(datetime.utcnow().timestamp())}"

        if req.action == "SELL":
            locate = self.check_locates(symbol)
            if not locate.get("locates_available", False):
                return {
                    "status": "rejected",
                    "reason": "No locates available",
                    "symbol": symbol,
                    "locate": locate,
                }

        trade_result = {
            "status": status,
            "bot": self.config.name,
            "ticker": symbol,
            "action": req.action,
            "qty": req.qty,
            "price": req.price,
            "mode": req.mode,
            "broker": req.broker,
            "order_id": order_id,
            "strategy": "Cygnus_Relative_Value_Arb",
            "timestamp": datetime.utcnow().isoformat(),
        }

        self._persist_trade(trade_result)
        self._notify_discord_trade(trade_result)
        return trade_result

    def _persist_trade(self, trade: dict[str, Any]) -> None:
        price = float(trade.get("price") or 0.0)
        qty = float(trade.get("qty") or 0.0)
        value = round(price * qty, 2)
        action = str(trade.get("action", "HOLD")).upper()

        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                try:
                    cursor.execute(
                        """
                        INSERT INTO trades_history
                        (ticker, action, shares, price, value, timestamp, status, order_id, strategy, bot_name, trade_mode)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            str(trade.get("ticker", "")).upper(),
                            action,
                            int(qty),
                            price,
                            value,
                            datetime.utcnow(),
                            str(trade.get("status", "simulated")).upper(),
                            str(trade.get("order_id", "")) or None,
                            str(trade.get("strategy", "Cygnus_Relative_Value_Arb")),
                            self.config.name,
                            str(trade.get("mode", "paper")).lower(),
                        ),
                    )
                except Exception:
                    cursor.execute(
                        """
                        INSERT INTO trades_history
                        (ticker, action, shares, price, value, timestamp, status, order_id, strategy)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            str(trade.get("ticker", "")).upper(),
                            action,
                            int(qty),
                            price,
                            value,
                            datetime.utcnow(),
                            str(trade.get("status", "simulated")).upper(),
                            str(trade.get("order_id", "")) or None,
                            str(trade.get("strategy", "Cygnus_Relative_Value_Arb")),
                        ),
                    )

                try:
                    cursor.execute(
                        """
                        INSERT INTO performance_metrics
                        (date, total_trades, buy_trades, sell_trades, total_value, strategy, bot_name)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            date.today(),
                            1,
                            1 if action == "BUY" else 0,
                            1 if action == "SELL" else 0,
                            value,
                            "Cygnus_Relative_Value_Arb",
                            self.config.name,
                        ),
                    )
                except Exception:
                    cursor.execute(
                        """
                        INSERT INTO performance_metrics
                        (date, total_trades, buy_trades, sell_trades, total_value, strategy)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            date.today(),
                            1,
                            1 if action == "BUY" else 0,
                            1 if action == "SELL" else 0,
                            value,
                            "Cygnus_Relative_Value_Arb",
                        ),
                    )
            conn.commit()
        except Exception as exc:
            logger.warning("MySQL persistence failed: %s", exc)
        finally:
            if conn is not None:
                conn.close()

    def _notify_discord_trade(self, trade: dict[str, Any]) -> None:
        try:
            from frontend.utils.discord_notify import notify_trade

            notify_trade(
                bot_name=self.config.name,
                symbol=str(trade.get("ticker", "")).upper(),
                side=str(trade.get("action", "")).lower(),
                qty=float(trade.get("qty", 0)),
                status=str(trade.get("status", "simulated")),
                mode=str(trade.get("mode", "paper")),
                ticket=str(trade.get("order_id", "")) or None,
                broker=str(trade.get("broker", "ibkr")),
                fund_name=self.config.fund,
            )
        except Exception as exc:
            logger.warning("Discord notification failed: %s", exc)

    def train_model(self, req: TrainRequest) -> dict[str, Any]:
        # Placeholder that logs training intent and hyperparameters for future Siamese training jobs.
        response = {
            "status": "training_started",
            "bot": self.config.name,
            "model": self.config.ml_model,
            "pair_id": req.pair_id,
            "window_size": req.window_size,
            "epochs": req.epochs,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if mlflow is not None and self.config.enable_mlflow_logging:
            try:
                mlflow.set_tracking_uri(self.config.mlflow_tracking_uri)
                mlflow.set_experiment(self.config.mlflow_experiment)
                with mlflow.start_run(run_name=f"cygnus_train_{req.pair_id}"):
                    mlflow.set_tag("bot", self.config.name)
                    mlflow.set_tag("phase", "training")
                    mlflow.log_param("model", self.config.ml_model)
                    mlflow.log_param("pair_id", req.pair_id)
                    mlflow.log_param("window_size", req.window_size)
                    mlflow.log_param("epochs", req.epochs)
                    mlflow.log_metric("training_request", 1)
                    run_id = mlflow.active_run().info.run_id if mlflow.active_run() else None
                response["mlflow"] = {
                    "logged": True,
                    "experiment": self.config.mlflow_experiment,
                    "run_id": run_id,
                }
            except Exception as exc:
                response["mlflow"] = {"logged": False, "reason": str(exc)}
        else:
            response["mlflow"] = {"logged": False, "reason": "mlflow unavailable or disabled"}

        return response


cygnus_bot = CygnusBot()
app = FastAPI(
    title="Cygnus Bot API",
    description=(
        "Relative value arbitrage service surface for Mansa Short Fund with "
        "Bollinger/SMI/cointegration/RSI divergence analytics, NLP scoring, "
        "Discord notifications, MySQL persistence, and MLflow logging."
    ),
    version="1.0.0",
)


@app.get("/cygnus/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "bot": cygnus_bot.config.name,
        "runtime_name": cygnus_bot.config.runtime_name,
        "fund": cygnus_bot.config.fund,
        "strategy": cygnus_bot.config.strategy,
        "ml_model": cygnus_bot.config.ml_model,
        "mlflow_tracking_uri": cygnus_bot.config.mlflow_tracking_uri,
        "dependencies": {
            "mlflow": mlflow is not None,
            "statsmodels": statsmodels_stattools is not None,
            "ib_insync": ib_insync is not None,
        },
    }


@app.post("/cygnus/analyze")
def analyze(req: PairAnalysisRequest) -> dict[str, Any]:
    return cygnus_bot.analyze_pair(req)


@app.post("/cygnus/locates")
def locates(symbol: str) -> dict[str, Any]:
    return cygnus_bot.check_locates(symbol)


@app.post("/cygnus/margin")
def margin(req: TradeRequest) -> dict[str, Any]:
    price = float(req.price or 0.0)
    return cygnus_bot.margin_check(price=price, qty=req.qty)


@app.post("/cygnus/trade")
def trade(req: TradeRequest) -> dict[str, Any]:
    return cygnus_bot.execute_trade(req)


@app.post("/cygnus/train")
def train(req: TrainRequest) -> dict[str, Any]:
    return cygnus_bot.train_model(req)


@app.get("/cygnus/predict")
def predict() -> dict[str, Any]:
    return {
        "status": "ok",
        "bot": cygnus_bot.config.name,
        "model": cygnus_bot.config.ml_model,
        "signal": "short_bias",
        "note": "Call /cygnus/analyze with pair inputs for live inference.",
    }
