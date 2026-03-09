"""Configuration for prediction analytics microservices."""
import os
from dataclasses import dataclass


@dataclass
class Settings:
    db_host: str = os.getenv("BENTLEY_DB_HOST", "127.0.0.1")
    db_port: int = int(os.getenv("BENTLEY_DB_PORT", "3307"))
    db_name: str = os.getenv("BENTLEY_DB_NAME", "mansa_bot")
    db_user: str = os.getenv("BENTLEY_DB_USER", "root")
    db_password: str = os.getenv("BENTLEY_DB_PASSWORD", "root")
    calc_methods: str = os.getenv("CALCULATION_METHODS", "lmsr,amm,orderbook")
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
    sentiment_min: float = float(os.getenv("MIN_SENTIMENT_SCORE", "0.3"))
    max_position_size: float = float(os.getenv("MAX_POSITION_SIZE", "100"))
    paper_trading: bool = os.getenv("PAPER_TRADING", "true").lower() == "true"
    bot_id: str = os.getenv("BOT_ID", "passive-income-bot-v1")


settings = Settings()
