from __future__ import annotations

import json
from typing import Any

import requests

try:
    import gradio as gr
except ImportError as exc:
    raise RuntimeError(
        "Gradio is required for this tester. Install with: pip install gradio"
    ) from exc


BOTS = [
    "Titan",
    "Vega",
    "Rigel",
    "Dogon",
    "Orion",
    "Draco",
    "Altair",
    "Procryon",
    "Hydra",
    "Triton",
    "Dione",
    "Cephei",
    "Rhea",
    "Jupicita",
    "Cygnus",
]


ACTIONS = [
    "health",
    "status",
    "analyze",
    "trade_dry_run",
    "signals",
    "coverage",
]


def _call_api(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        if method == "GET":
            response = requests.get(url, timeout=20)
        else:
            response = requests.post(url, json=payload or {}, timeout=20)

        result: dict[str, Any] = {
            "status_code": response.status_code,
            "ok": response.ok,
            "url": url,
        }
        try:
            result["response"] = response.json()
        except ValueError:
            result["response"] = response.text[:5000]
        return result
    except requests.RequestException as exc:
        return {
            "status_code": None,
            "ok": False,
            "url": url,
            "error": str(exc),
        }


def run_test(
    base_url: str,
    bot: str,
    action: str,
    ticker: str,
    side: str,
    qty: float,
    broker: str,
    headline: str,
) -> str:
    root = (base_url or "http://127.0.0.1:5001").rstrip("/")
    bot_path = bot.lower()

    if action == "coverage":
        result = _call_api("GET", f"{root}/bots/endpoints/coverage")
        return json.dumps(result, indent=2, default=str)

    if action == "signals":
        result = _call_api("GET", f"{root}/signals/{bot}")
        return json.dumps(result, indent=2, default=str)

    if action == "health":
        result = _call_api("GET", f"{root}/{bot_path}/health")
        return json.dumps(result, indent=2, default=str)

    if action == "status":
        result = _call_api("GET", f"{root}/{bot_path}/status")
        return json.dumps(result, indent=2, default=str)

    if action == "analyze":
        payload = {
            "ticker": ticker.strip().upper() or "SPY",
            "news_headlines": [headline] if headline.strip() else [],
            "context": {},
        }
        result = _call_api("POST", f"{root}/{bot_path}/analyze", payload)
        return json.dumps(result, indent=2, default=str)

    if action == "trade_dry_run":
        payload = {
            "broker": broker.strip() or "paper",
            "ticker": ticker.strip().upper() or "SPY",
            "action": side.strip().upper() or "BUY",
            "qty": float(qty),
            "dry_run": True,
        }
        result = _call_api("POST", f"{root}/{bot_path}/trade", payload)
        return json.dumps(result, indent=2, default=str)

    return json.dumps({"error": f"Unsupported action: {action}"}, indent=2)


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="Bentley FastAPI Bot Tester") as demo:
        gr.Markdown(
            "# Bentley FastAPI Bot Tester\n"
            "Use this Gradio surface for interactive endpoint checks.\n"
            "For polished reporting, use Streamlit Admin Control Center and Vercel dashboards."
        )

        with gr.Row():
            base_url = gr.Textbox(
                label="FastAPI Base URL",
                value="http://127.0.0.1:5001",
            )
            bot = gr.Dropdown(label="Bot", choices=BOTS, value="Titan")
            action = gr.Dropdown(label="Action", choices=ACTIONS, value="coverage")

        with gr.Row():
            ticker = gr.Textbox(label="Ticker", value="SPY")
            side = gr.Dropdown(label="Side", choices=["BUY", "SELL"], value="BUY")
            qty = gr.Number(label="Qty", value=1)
            broker = gr.Textbox(label="Broker", value="paper")

        headline = gr.Textbox(
            label="Optional Headline",
            placeholder="Strong earnings beat raises growth outlook",
        )

        output = gr.Code(label="API Response", language="json")

        run_btn = gr.Button("Run")
        run_btn.click(
            fn=run_test,
            inputs=[base_url, bot, action, ticker, side, qty, broker, headline],
            outputs=[output],
        )

    return demo


if __name__ == "__main__":
    app = build_demo()
    app.launch(server_name="0.0.0.0", server_port=7860, share=True)
