"""Demo/Testing configuration for Demo_Bots database on port 3307."""
import os

class DemoConfig:
    """Configuration for Demo_Bots testing environment."""
    MYSQL_HOST = os.getenv("DEMO_MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("DEMO_MYSQL_PORT", 3307))
    MYSQL_USER = os.getenv("DEMO_MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("DEMO_MYSQL_PASSWORD", "root")
    MYSQL_DB = os.getenv("DEMO_MYSQL_DB", "mansa_bot")

    POLYMARKET_API = "https://gamma-api.polymarket.com"
    KALSHI_API = "https://api.kalshi.com"


class Config:
    """Production configuration for Bentley_Bot on port 3307 (Docker)."""
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3307))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
    MYSQL_DB = os.getenv("MYSQL_DB", "mansa_bot")

    POLYMARKET_API = "https://gamma-api.polymarket.com"
    KALSHI_API = "https://api.kalshi.com"
