"""
Bot 9: Dogon

Fund: Mansa ETF
Strategy: Portfolio Optimizer
"""

import optuna
import gradio as gr
import numpy as np


def start():
    """Start the bot."""
    print("Starting Dogon (Mansa ETF)")


def stop():
    """Stop the bot."""
    print("Stopping Dogon (Mansa ETF)")


def get_status():
    """Get bot status."""
    return {
        "id": 9,
        "name": "Dogon",
        "fund": "Mansa ETF",
        "strategy": "Portfolio Optimizer",
        "status": "idle",
    }


def configure(config):
    """Configure bot parameters."""
    print(f"Configuring Dogon with: {config}")


def tune_xgboost_hyperparams(n_trials=10):
    def objective(trial):
        max_depth = trial.suggest_int("max_depth", 3, 10)
        learning_rate = trial.suggest_float("learning_rate", 0.01, 0.3)
        subsample = trial.suggest_float("subsample", 0.5, 1.0)
        # Dummy Sharpe ratio proxy
        return max_depth * learning_rate * subsample

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)
    return study.best_params


def gradio_etf_optimizer():
    def optimize(weights):
        # Dummy: normalize weights
        arr = np.array(weights)
        arr = arr / arr.sum()
        return arr.tolist()

    demo = gr.Interface(
        fn=optimize,
        inputs=gr.inputs.Dataframe(
            headers=["ETF1", "ETF2", "ETF3"], type="numpy"
        ),
        outputs="dataframe",
        title="Dogon ETF Optimizer",
    )
    demo.launch(share=True)


if __name__ == "__main__":
    print("Dogon | Mansa ETF | Portfolio Optimizer - Ready")