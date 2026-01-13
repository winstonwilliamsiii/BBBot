#Gold_RSI trading on Alpaca Paper Trading Account

import os
import time
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from alpaca_trade_api import REST, TimeFrame

ALPACA_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"

alpaca = REST(ALPACA_KEY, ALPACA_SECRET, base_url=ALPACA_BASE_URL)

GOLD_SYMBOL = "GLD"  # proxy for gold futures
USD_COP_SYMBOL = "USD_COP_SIM"  # logical symbol; simulated or external
RSI_PERIOD = 14
RISK_PER_TRADE = 0.01  # 1% of equity
