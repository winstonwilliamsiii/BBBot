import requests
import os

def send_discord_trade_notification(symbol, side, qty, order_type, limit_price=None, status=None, webhook_url=None):
    """
    Send a Discord notification for an Alpaca trade via webhook.
    """
    if webhook_url is None:
        webhook_url = os.getenv("DISCORD_ALPACA_WEBHOOK")
    if not webhook_url:
        return False
    color = 3066993 if side.lower() == "buy" else 15158332
    embed = {
        "title": f"Alpaca Trade: {side.upper()} {symbol}",
        "description": (
            f"Order Type: {order_type}\n"
            f"Qty: {qty}\n"
            f"Limit Price: {limit_price if limit_price else 'Market'}\n"
            f"Status: {status if status else 'Submitted'}"
        ),
        "color": color,
    }
    payload = {"embeds": [embed]}
    try:
        resp = requests.post(webhook_url, json=payload, timeout=5)
        return resp.status_code in (200, 204)
    except requests.RequestException:
        return False
