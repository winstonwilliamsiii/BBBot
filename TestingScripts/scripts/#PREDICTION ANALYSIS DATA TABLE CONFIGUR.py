#PREDICTION ANALYSIS DATA TABLE CONFIGURATION 

import os

class Config:
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3307))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")
    MYSQL_DB = os.getenv("MYSQL_DB", "Demo_Bots")

    POLYMARKET_API = "https://gamma-api.polymarket.com"
    KALSHI_API = "https://api.kalshi.com"
    