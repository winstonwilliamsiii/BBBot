"""Root entrypoint for Rhea bot analysis and Gradio launcher.

Mirrors altair_main.py — provides:
  - MLflow-logged ticker analysis via RheaBot.analyze_ticker()
  - Optuna hyperparameter sweep logged to MLflow (Rhea_Mansa_ADI experiment)
  - Health/status snapshot tab
  - Gradio UI: single-file launch for demos and paper-trade workflows
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import gradio as gr
import matplotlib.pyplot as plt
import optuna

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "bots") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "bots"))


def _load_rhea_bot():
    from bots.rhea_bot import RheaBot, RheaConfig  # noqa: WPS433

    return RheaBot, RheaConfig


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


# ---------------------------------------------------------------------------
# Chart helper
# ---------------------------------------------------------------------------

def _chart_analysis(result: dict[str, Any]):
    """Build a two-panel chart from analysis result."""
    technical = result.get("technical", {})

    fig, (ax_levels, ax_score) = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(12, 4),
        gridspec_kw={"width_ratios": [2.2, 1.2]},
    )

    symbol = result.get("ticker", "N/A")
    ax_levels.set_title(f"{symbol} Technical Levels")
    ax_levels.axhline(
        technical.get("sma_20", 0.0),
        color="royalblue",
        label="SMA 20",
    )
    ax_levels.axhline(
        technical.get("ema_20", 0.0),
        color="seagreen",
        label="EMA 20",
    )
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
    return fig


# ---------------------------------------------------------------------------
# Core analysis helper
# ---------------------------------------------------------------------------

def run_analysis(symbol: str, headlines: str, log_mlflow: bool = True):
    """Analyze ticker and return (chart, summary, json)."""
    RheaBot, RheaConfig = _load_rhea_bot()
    config = RheaConfig.from_env()
    bot = RheaBot(config)
    parsed_headlines = [
        line.strip()
        for line in str(headlines).splitlines()
        if line.strip()
    ]
    result = bot.analyze_ticker(
        symbol.strip().upper(),
        headlines=parsed_headlines,
        log_to_mlflow=log_mlflow,
    )

    fig = _chart_analysis(result)
    action = str(result.get("action", "HOLD"))
    summary = (
        f"Action: {action}\n"
        f"Composite score: "
        f"{float(result.get('composite_score', 0.0)):.4f}\n"
        f"Ticker: {result.get('ticker', symbol.strip().upper())}"
    )
    details = json.dumps(result, indent=2, default=str)

    return fig, summary, details


# ---------------------------------------------------------------------------
# Optuna sweep (XGBoost proxy objective)
# ---------------------------------------------------------------------------

def _rhea_objective_score(
    n_estimators: int,
    max_depth: int,
    learning_rate: float,
) -> float:
    """Proxy objective that approximates Rhea's XGBoost sweet-spot."""
    est_score = max(0.0, 1.0 - abs(n_estimators - 120) / 300.0)
    depth_score = max(0.0, 1.0 - abs(max_depth - 4) / 8.0)
    lr_score = max(0.0, 1.0 - abs(learning_rate - 0.08) / 0.29)
    return round((est_score * 0.40 + depth_score * 0.35 + lr_score * 0.25), 6)


def _optuna_objective(trial: optuna.Trial) -> float:
    n_estimators = trial.suggest_int("n_estimators", 60, 400)
    max_depth = trial.suggest_int("max_depth", 2, 10)
    learning_rate = trial.suggest_float("learning_rate", 0.01, 0.30)

    score = _rhea_objective_score(n_estimators, max_depth, learning_rate)

    RheaBot, RheaConfig = _load_rhea_bot()
    _ = RheaBot  # Imported for consistency with run-analysis paths.
    config = RheaConfig.from_env()

    import mlflow

    mlflow.set_tracking_uri(config.mlflow_tracking_uri)
    mlflow.set_experiment(config.mlflow_experiment)

    with mlflow.start_run(
        run_name=f"rhea-optuna-{datetime.now(timezone.utc).isoformat()}"
    ):
        mlflow.set_tag("bot", "Rhea")
        mlflow.set_tag("fund", config.fund)
        mlflow.set_tag("sweep", "optuna-xgboost")
        mlflow.log_params(
            {
                "n_estimators": n_estimators,
                "max_depth": max_depth,
                "learning_rate": learning_rate,
            }
        )
        mlflow.log_metric("score", score)

    return score


def run_optuna_sweep(n_trials: int = 20) -> tuple[dict, float]:
    study = optuna.create_study(direction="maximize")
    study.optimize(_optuna_objective, n_trials=n_trials)
    return study.best_params, round(study.best_value, 6)


# ---------------------------------------------------------------------------
# Gradio tab helpers
# ---------------------------------------------------------------------------

def _gradio_analyze(symbol: str, headlines: str, log_mlflow: bool):
    if not symbol.strip():
        fig, _ = plt.subplots()
        return fig, "Error: Stock symbol is required.", '{}'
    return run_analysis(symbol, headlines, log_mlflow=log_mlflow)


def _gradio_optuna(n_trials: int) -> str:
    best_params, best_value = run_optuna_sweep(n_trials=n_trials)
    return json.dumps(
        {"best_params": best_params, "best_value": best_value},
        indent=2,
    )


def _gradio_health() -> str:
    RheaBot, RheaConfig = _load_rhea_bot()
    config = RheaConfig.from_env()
    bot = RheaBot(config)
    snapshot = bot.health_snapshot(probe_fastapi=False)
    return json.dumps(snapshot, indent=2, default=str)


def _gradio_bootstrap() -> str:
    RheaBot, RheaConfig = _load_rhea_bot()
    config = RheaConfig.from_env()
    bot = RheaBot(config)
    result = bot.bootstrap_demo_state()
    return json.dumps(result, indent=2, default=str)


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

def launch_gradio(share: bool = False) -> None:
    default_log_mlflow = not _truthy(os.getenv("RHEA_NO_DOCKER_MODE", "false"))

    with gr.Blocks(title="Rhea Bot — MLflow + Gradio") as demo:
        gr.Markdown(
            "## Rhea Bot — Mansa ADI · Intra-Day / Swing\n"
            "Aerospace, Defense & Industrials paper-trade analysis.\n"
            "MLflow experiment: **Rhea_Mansa_ADI**"
        )

        # --- Analysis tab ---
        with gr.Tab("Ticker Analysis"):
            with gr.Row():
                sym_in = gr.Textbox(
                    label="Stock Symbol",
                    placeholder="e.g. GD, AXON, NOC",
                    value="GD",
                )
                log_chk = gr.Checkbox(
                    label="Log to MLflow",
                    value=default_log_mlflow,
                )
            headlines_in = gr.Textbox(
                label="News Headlines (one per line)",
                lines=6,
                placeholder=(
                    "Defense contract award boosts order backlog\n"
                    "Industrial growth supports suppliers"
                ),
            )
            analyze_btn = gr.Button("Run Analysis", variant="primary")
            analysis_chart = gr.Plot(label="Technical Chart")
            analysis_summary = gr.Textbox(
                label="Signal Summary",
                lines=3,
            )
            analysis_json = gr.Code(
                language="json",
                label="Raw Analysis JSON",
            )
            analyze_btn.click(  # type: ignore[attr-defined]
                fn=_gradio_analyze,
                inputs=[sym_in, headlines_in, log_chk],
                outputs=[analysis_chart, analysis_summary, analysis_json],
            )

        # --- Bootstrap tab ---
        with gr.Tab("Bootstrap Demo"):
            gr.Markdown(
                "Run a preset demo analysis using the first ticker in Rhea's "
                "screener universe — no MLflow logging."
            )
            bootstrap_btn = gr.Button("Run Bootstrap Demo")
            bootstrap_out = gr.Code(language="json", label="Bootstrap Result")
            bootstrap_btn.click(  # type: ignore[attr-defined]
                fn=_gradio_bootstrap,
                inputs=[],
                outputs=bootstrap_out,
            )

        # --- Optuna sweep tab ---
        with gr.Tab("Optuna Sweep (XGBoost)"):
            gr.Markdown(
                "Runs an Optuna hyperparameter sweep against a proxy objective "
                "that approximates Rhea's XGBoost sweet-spot. Each trial is "
                "logged to the **Rhea_Mansa_ADI** MLflow experiment."
            )
            trials_slider = gr.Slider(
                minimum=5,
                maximum=100,
                value=20,
                step=5,
                label="Number of Trials",
            )
            sweep_btn = gr.Button("Run Sweep", variant="primary")
            sweep_out = gr.Code(language="json", label="Best Params + Score")
            sweep_btn.click(  # type: ignore[attr-defined]
                fn=_gradio_optuna,
                inputs=[trials_slider],
                outputs=sweep_out,
            )

        # --- Health tab ---
        with gr.Tab("Health Snapshot"):
            gr.Markdown(
                "Checks MLflow, MySQL, Airflow, Airbyte, and Discord connectivity."
            )
            health_btn = gr.Button("Refresh Health")
            health_out = gr.Code(language="json", label="Health Snapshot")
            health_btn.click(  # type: ignore[attr-defined]
                fn=_gradio_health,
                inputs=[],
                outputs=health_out,
            )

    demo.launch(
        share=share,
        server_name="127.0.0.1",
        server_port=7860,
        inbrowser=False,
    )


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    launch_gradio()
