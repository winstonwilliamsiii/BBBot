"""Triton bot compatibility wrapper for the shared runtime module."""

import optuna
import gradio as gr
from triton_bot import TritonBot


_BOT = TritonBot()


def tune_sector_model(n_trials=10):
    def objective(trial):
        param = trial.suggest_float("sector_param", 0.1, 1.0)
        # Dummy sector score
        return param

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)
    return study.best_params


def gradio_sector_dashboard():
    def test_strategy(x):
        return f"Sector strategy test: {x}"

    demo = gr.Interface(
        fn=test_strategy,
        inputs="number",
        outputs="text",
        title="Triton Sector Dashboard",
    )
    demo.launch(share=True)


def start():
    """Start the bot."""
    return _BOT.bootstrap_demo_state()


def stop():
    """Stop the bot."""
    return {"status": "stopped", "name": "Triton"}


def get_status():
    """Get bot status."""
    return _BOT.status()


def configure(config):
    """Configure bot parameters."""
    return _BOT.configure(config)


if __name__ == "__main__":
    print(_BOT.bootstrap_demo_state())