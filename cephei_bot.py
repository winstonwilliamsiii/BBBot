"""Cephei Bot FastAPI service.

Options and CFD API with ML signal generation, regime filtering,
and execution hooks for broker integration.
"""

from __future__ import annotations

import logging
import os
from typing import List

import lightgbm as lgb
import mysql.connector
import numpy as np
import optuna
import requests
import torch
import torch.nn as nn
from arch import arch_model
from fastapi import FastAPI
from pydantic import BaseModel, Field

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("cephei_bot")

app = FastAPI(title="Cephei_Bot", version="1.0.0")


# -----------------------------
# ENV CONFIGURATION
# -----------------------------
IBKR_API_URL = os.getenv("IBKR_API_URL", "https://api.ibkr.com/v1/cfd/options")
FOREXVPS_ENDPOINT = os.getenv("FOREXVPS_ENDPOINT", "https://forexvps.net/execution")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "10"))
VOL_REGIME_MODEL_PATH = os.getenv("VOL_REGIME_MODEL_PATH", "models/vol_regime.txt")
SIAMESE_WEIGHTS_PATH = os.getenv("SIAMESE_WEIGHTS_PATH", "")
ENABLE_DB_LOGGING = os.getenv("ENABLE_DB_LOGGING", "false").lower() == "true"

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "cephei_logs"),
}


# -----------------------------
# DATA MODELS
# -----------------------------
class OptionData(BaseModel):
    ticker: str = Field(..., min_length=1)
    strike: float
    expiry: str
    price: float
    underlying_price: float
    returns: List[float] = Field(..., min_length=10)


# -----------------------------
# ML HEAD – Siamese Network
# -----------------------------
class SiameseVolNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.iv_branch = nn.Sequential(
            nn.Linear(5, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
        )
        self.rv_branch = nn.Sequential(
            nn.Linear(5, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
        )
        self.fc = nn.Sequential(
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid(),
        )

    def forward(self, iv_input: torch.Tensor, rv_input: torch.Tensor) -> torch.Tensor:
        iv_feat = self.iv_branch(iv_input)
        rv_feat = self.rv_branch(rv_input)
        combined = torch.cat((iv_feat, rv_feat), dim=1)
        return self.fc(combined)


MODEL = SiameseVolNet()
MODEL.eval()

if SIAMESE_WEIGHTS_PATH and os.path.exists(SIAMESE_WEIGHTS_PATH):
    try:
        MODEL.load_state_dict(torch.load(SIAMESE_WEIGHTS_PATH, map_location="cpu"))
        MODEL.eval()
        logger.info("Loaded Siamese weights from %s", SIAMESE_WEIGHTS_PATH)
    except (OSError, RuntimeError, ValueError) as exc:
        logger.warning("Failed to load Siamese weights: %s", exc)


# -----------------------------
# VOL FORECAST – GARCH/EWMA
# -----------------------------
def ewma_vol(returns: List[float], lambda_: float = 0.94) -> float:
    returns_arr = np.array(returns, dtype=np.float64)
    weights = np.array([(1 - lambda_) * lambda_**i for i in range(len(returns_arr))], dtype=np.float64)
    weights = weights / np.sum(weights)
    return float(np.sqrt(np.sum(weights * returns_arr**2)))


def forecast_realized_vol(returns: List[float]) -> float:
    if len(returns) < 30:
        return ewma_vol(returns)

    try:
        model = arch_model(returns, vol="GARCH", p=1, q=1)
        result = model.fit(disp="off")
        return float(result.conditional_volatility.iloc[-1])
    except (ValueError, FloatingPointError, np.linalg.LinAlgError) as exc:
        logger.warning("GARCH failed; falling back to EWMA. Reason: %s", exc)
        return ewma_vol(returns)


# -----------------------------
# REGIME CLASSIFIER – LightGBM
# -----------------------------
def classify_vol_regime(features: List[float], model_path: str = VOL_REGIME_MODEL_PATH) -> str:
    if not os.path.exists(model_path):
        logger.warning("Regime model not found at %s; defaulting to Low-Vol", model_path)
        return "Low-Vol"

    model = lgb.Booster(model_file=model_path)
    pred = model.predict(np.array(features).reshape(1, -1))
    return "High-Vol" if float(pred[0]) > 0.5 else "Low-Vol"


# -----------------------------
# OPTUNA – Hyperparameter Tuning
# -----------------------------
def optimize_siamese(trial: optuna.Trial) -> float:
    lr = trial.suggest_float("lr", 1e-5, 1e-2, log=True)
    model = SiameseVolNet()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()

    for _ in range(10):
        iv = torch.rand((8, 5))
        rv = torch.rand((8, 5))
        target = torch.rand((8, 1))
        output = model(iv, rv)
        loss = loss_fn(output, target)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    return float(loss.item())


def run_optuna_study() -> dict:
    study = optuna.create_study(direction="minimize")
    study.optimize(optimize_siamese, n_trials=20)
    return study.best_params


# -----------------------------
# EXECUTION LAYER
# -----------------------------
def execute_delta_neutral(ticker: str, signal: str) -> dict:
    payload = {
        "ticker": ticker,
        "signal": signal,
        "hedge": "delta-neutral",
        "execution_endpoint": FOREXVPS_ENDPOINT,
    }
    try:
        response = requests.post(IBKR_API_URL, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        result = response.json()
    except requests.RequestException as exc:
        logger.error("Execution request failed: %s", exc)
        return {"status": "error", "detail": str(exc)}
    try:
        from frontend.utils.discord_notify import notify_trade
        notify_trade(
            bot_name="Cephei",
            symbol=ticker,
            side="buy" if signal.lower() in ("buy", "long") else "sell",
            qty=1,
            status=result.get("status", "submitted"),
            mode="live",
            broker="ibkr",
            fund_name="Mansa Functions Options",
        )
    except Exception:
        pass
    return result


def monitor_greeks(ticker: str) -> dict:
    return {
        "ticker": ticker,
        "vega": 0.12,
        "gamma": 0.03,
        "theta": -0.01,
    }


# -----------------------------
# DATABASE LOGGING
# -----------------------------
def log_to_db(entry: str) -> None:
    if not ENABLE_DB_LOGGING:
        return

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO logs (entry) VALUES (%s)", (entry,))
        conn.commit()
    except mysql.connector.Error as exc:
        logger.error("Failed to write DB log: %s", exc)
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


# -----------------------------
# API ENDPOINTS
# -----------------------------
@app.post("/analyze")
def analyze_option(data: OptionData) -> dict:
    iv_input = torch.tensor(
        [[data.price, data.strike, data.underlying_price, 0.0, 0.0]],
        dtype=torch.float32,
    )

    rv_forecast = forecast_realized_vol(data.returns)
    rv_input = torch.tensor(
        [[rv_forecast, float(np.mean(data.returns)), float(np.std(data.returns)), 0.0, 0.0]],
        dtype=torch.float32,
    )

    with torch.no_grad():
        mispricing_score = float(MODEL(iv_input, rv_input).item())

    regime = classify_vol_regime([mispricing_score, rv_forecast])
    greeks = monitor_greeks(data.ticker)

    if regime == "High-Vol" and mispricing_score > 0.6:
        trade = execute_delta_neutral(data.ticker, "enter")
    else:
        trade = {"status": "hold"}

    result = {
        "ticker": data.ticker,
        "mispricing_score": mispricing_score,
        "regime": regime,
        "greeks": greeks,
        "trade_action": trade,
    }
    log_to_db(f"analyze:{data.ticker}:{mispricing_score:.4f}:{regime}")
    return result


@app.post("/optuna_tune")
def tune_model() -> dict:
    best_params = run_optuna_study()
    return {"best_params": best_params}


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "service": "Cephei_Bot",
        "ibkr_api_url": IBKR_API_URL,
        "forexvps_endpoint": FOREXVPS_ENDPOINT,
        "db_logging": ENABLE_DB_LOGGING,
    }
