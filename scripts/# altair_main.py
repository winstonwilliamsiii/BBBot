# altair_main.py

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if str(REPO_ROOT / "bots") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "bots"))

from altair_bot import AltairBot, AltairConfig
import optuna
import mlflow
import gradio as gr


def train_and_eval_xgboost(max_depth, learning_rate, n_estimators):
    """Lightweight placeholder objective score for demo tuning flows."""
    depth_score = max(0.0, 1.0 - abs(float(max_depth) - 6.0) / 10.0)
    lr_score = max(0.0, 1.0 - abs(float(learning_rate) - 0.08) / 0.3)
    est_score = max(0.0, 1.0 - abs(float(n_estimators) - 250.0) / 500.0)
    return (depth_score + lr_score + est_score) / 3.0

def run_analysis(symbol, headlines):
    config = AltairConfig.from_env()
    bot = AltairBot(config)
    analysis = bot.analyze_ticker(symbol, headlines=headlines, log_to_mlflow=True)
    return analysis

def optuna_objective(trial):
    # Example hyperparameters for XGBoost
    max_depth = trial.suggest_int("max_depth", 3, 10)
    learning_rate = trial.suggest_float("learning_rate", 0.01, 0.3)
    n_estimators = trial.suggest_int("n_estimators", 100, 500)

    # Train/evaluate ensemble here
    score = train_and_eval_xgboost(max_depth, learning_rate, n_estimators)
    mlflow.log_params({"max_depth": max_depth, "learning_rate": learning_rate, "n_estimators": n_estimators})
    mlflow.log_metric("score", score)
    return score

def run_optuna():
    study = optuna.create_study(direction="maximize")
    study.optimize(optuna_objective, n_trials=20)
    return study.best_params, study.best_value

def launch_gradio():
    def interface(symbol, headlines):
        return run_analysis(symbol, headlines)

    iface = gr.Interface(
        fn=interface,
        inputs=[gr.Textbox(label="Stock Symbol"), gr.Textbox(label="Headlines")],
        outputs="text"
    )
    iface.launch()

if __name__ == "__main__":
    launch_gradio()