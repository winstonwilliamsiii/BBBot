from __future__ import annotations

import json
from typing import Any

import gradio as gr
import matplotlib.pyplot as plt

try:
    from bots.rhea_bot import RheaBot, RheaConfig
except Exception:
    RheaBot = None
    RheaConfig = None


def _mock_result(ticker: str) -> dict[str, Any]:
    return {
        "ticker": ticker,
        "technical": {
            "sma_20": 527.3155,
            "ema_20": 528.1451,
            "bollinger_upper": 547.3245,
            "bollinger_lower": 507.3065,
            "last_close": 510.95,
        },
        "composite_score": 0.231,
        "buy_threshold": 0.18,
        "sell_threshold": -0.18,
        "model_stack": {
            "random_forest_vote": 1.0,
            "xgboost_vote": 1.0,
            "torch_vote": 0.41,
        },
        "action": "BUY",
    }


def _get_result(ticker: str) -> dict[str, Any]:
    normalized = str(ticker).strip().upper() or "GD"
    if RheaBot is None or RheaConfig is None:
        return _mock_result(normalized)

    try:
        bot = RheaBot(RheaConfig.from_env())
        return bot.analyze_ticker(normalized, headlines=[], log_to_mlflow=False)
    except Exception:
        return _mock_result(normalized)


def analyze_ticker(ticker: str):
    result = _get_result(ticker)
    technical = result.get("technical", {})

    fig, (ax_levels, ax_score) = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(12, 4),
        gridspec_kw={"width_ratios": [2.2, 1.2]},
    )

    symbol = result.get("ticker", str(ticker).strip().upper())
    ax_levels.set_title(f"{symbol} Technical Levels")
    ax_levels.axhline(technical.get("sma_20", 0.0), color="royalblue", label="SMA 20")
    ax_levels.axhline(technical.get("ema_20", 0.0), color="seagreen", label="EMA 20")
    ax_levels.axhline(
        technical.get("bollinger_upper", 0.0),
        color="crimson",
        linestyle="--",
        label="Bollinger Upper",
    )
    ax_levels.axhline(
        technical.get("bollinger_lower", 0.0),
        color="crimson",
        linestyle="--",
        label="Bollinger Lower",
    )
    ax_levels.axhline(
        technical.get("last_close", 0.0),
        color="black",
        linewidth=2,
        label="Last Close",
    )
    ax_levels.set_ylabel("Price")
    ax_levels.legend(loc="best")
    ax_levels.grid(alpha=0.25)

    ax_score.set_title("Signal Metrics")
    metric_names = ["Composite", "Buy Thresh", "Sell Thresh"]
    metric_vals = [
        float(result.get("composite_score", 0.0)),
        float(result.get("buy_threshold", 0.0)),
        float(result.get("sell_threshold", 0.0)),
    ]
    colors = ["tab:orange", "tab:green", "tab:red"]
    bars = ax_score.bar(metric_names, metric_vals, color=colors)
    ax_score.axhline(0.0, color="black", linewidth=1)
    ax_score.set_ylim(-1.0, 1.0)
    ax_score.grid(axis="y", alpha=0.25)
    for bar in bars:
        height = bar.get_height()
        ax_score.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + (0.03 if height >= 0 else -0.07),
            f"{height:.3f}",
            ha="center",
            va="bottom" if height >= 0 else "top",
            fontsize=9,
        )

    fig.tight_layout()

    action = str(result.get("action", "HOLD"))
    summary = (
        f"Action: {action}\n"
        f"Composite score: {float(result.get('composite_score', 0.0)):.4f}\n"
        f"Ticker: {symbol}"
    )
    details = json.dumps(result, indent=2, default=str)

    return fig, summary, details


demo = gr.Interface(
    fn=analyze_ticker,
    inputs=gr.Textbox(label="Enter Ticker", placeholder="e.g. GD, NOC, AXON"),
    outputs=[
        gr.Plot(label="Technical Chart"),
        gr.Textbox(label="Signal Summary", lines=4),
        gr.Code(label="Raw Analysis JSON", language="json"),
    ],
    title="Rhea Demo Gradio",
    description="Charts technical levels and signal metrics from Rhea analysis output.",
)

demo.launch(server_name="127.0.0.1", server_port=7862, inbrowser=False)
