#MLFLOW Logging Template
import mlflow
from datetime import datetime

def log_trade_to_mlflow(
    bot_name: str,
    ticker: str,
    side: str,
    dollar_amount: float,
    entry_price: float,
    strategy_label: str,
    extra_tags: dict = None
):
    mlflow.set_experiment("mansa_trades")

    with mlflow.start_run(run_name=f"{bot_name}_{ticker}_{datetime.utcnow().isoformat()}"):
        mlflow.log_param("bot_name", bot_name)
        mlflow.log_param("ticker", ticker)
        mlflow.log_param("side", side)
        mlflow.log_param("strategy_label", strategy_label)

        mlflow.log_metric("dollar_amount", dollar_amount)
        mlflow.log_metric("entry_price", entry_price)

        if extra_tags:
            for k, v in extra_tags.items():
                mlflow.set_tag(k, v)

if __name__ == "__main__":
    log_trade_to_mlflow(
        bot_name="Titan_Bot",
        ticker="NVDA",
        side="buy",
        dollar_amount=5000,
        entry_price=950.0,
        strategy_label="Tech_Fundamentals_Mag7",
        extra_tags={"universe": "Mag7+Tech", "screener": "Titan_Tech_Fundamentals"}
    )
