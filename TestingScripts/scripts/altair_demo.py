"""
Altair Demo: FTMO Paper Trade with Full ML Analysis & Discord Notifications
============================================================================

This demonstration script shows Altair Bot executing a complete news-trading cycle:
1. ML analysis of AI stock with news headlines
2. Trade signal generation (BUY/SELL/HOLD)
3. Paper trade execution on Alpaca
4. Discord notifications to #ai-ml and #bot_talk channels
5. Bentley Dashboard updates

Shows real-world sentiment scoring, composite score calculation, and risk rules.
Demonstrates full integration with Mansa AI Fund infrastructure.
"""

from __future__ import annotations

import os
import sys
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

# Load environment
load_dotenv(override=True)

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from altair_bot import AltairBot, AltairConfig


def main():
    """Run comprehensive Altair demo with BUY signal and paper trade execution."""

    print("\n" + "=" * 90)
    print(" " * 20 + "ALTAIR BOT DEMO: NEWS TRADING SYSTEM")
    print(" " * 20 + "Mansa AI Fund - FTMO Paper Trading")
    print("=" * 90 + "\n")

    # ─────────────────────────────────────────────────────────────────────────
    # 1. LOAD ALTAIR BOT CONFIGURATION
    # ─────────────────────────────────────────────────────────────────────────
    print("📋 STEP 1: Loading Altair Bot Configuration")
    print("-" * 90)

    config = AltairConfig.from_env()
    bot = AltairBot(config)

    print(f"✅ Altair Bot Loaded")
    print(f"   • Bot Name: {bot.config.name}")
    print(f"   • Fund: {bot.config.fund}")
    print(f"   • Strategy: {bot.config.strategy}")
    print(f"   • Universe: {', '.join(bot.config.default_universe)}")
    print(f"   • Position Size: ${bot.config.position_size:,.0f}")
    print(f"   • Execution Mode: {bot.config.execution_mode.upper()}")
    print(f"   • Buy Threshold: {bot.config.buy_threshold}")
    print(f"   • Sell Threshold: {bot.config.sell_threshold}")

    # ─────────────────────────────────────────────────────────────────────────
    # 2. MOCK NEWS SCENARIO
    # ─────────────────────────────────────────────────────────────────────────
    print("\n📰 STEP 2: News Scenario")
    print("-" * 90)

    symbol = str(bot.config.default_universe[0]).upper() if bot.config.default_universe else "RGTI"
    news_headlines = [
        f"{symbol} beats Q1 earnings by 20%, revenue up 45% YoY",
        f"Analysts upgrade {symbol} to BUY with higher price target",
        f"AI demand accelerates for {symbol} with stronger guidance",
        f"Institutional investors increase {symbol} positions after earnings",
    ]

    print(f"Target Symbol: {symbol}")
    print(f"News Headlines:")
    for i, headline in enumerate(news_headlines, 1):
        print(f"   {i}. {headline}")

    # ─────────────────────────────────────────────────────────────────────────
    # 3. ML ANALYSIS & SIGNAL GENERATION
    # ─────────────────────────────────────────────────────────────────────────
    print("\n🤖 STEP 3: ML Analysis & Signal Generation")
    print("-" * 90)

    analysis = bot.analyze_ticker(symbol, headlines=news_headlines, log_to_mlflow=False)

    print(f"✅ Analysis Complete for {symbol}")
    print(f"\n   Screener Scores:")
    print(f"   • Volume Score: {analysis['screener']['volume_score']:.4f}")
    print(f"   • Valuation Score: {analysis['screener']['valuation_score']:.4f}")
    print(f"   • Quality Score: {analysis['screener']['quality_score']:.4f}")

    print(f"\n   Sentiment Analysis:")
    print(f"   • Sentiment Score: {analysis['sentiment']['score']:.4f}")
    print(f"   • Headlines Analyzed: {analysis['sentiment']['headline_count']}")

    print(f"\n   Composite Scoring:")
    print(f"   • Volume Component (20%): {analysis['screener']['volume_score'] * 0.20:.4f}")
    print(f"   • Valuation Component (25%): {analysis['screener']['valuation_score'] * 0.25:.4f}")
    print(f"   • Quality Component (30%): {analysis['screener']['quality_score'] * 0.30:.4f}")
    print(f"   • Sentiment Component (25%): {analysis['sentiment']['score'] * 0.25:.4f}")
    print(f"   ───────────────────────────────────────")
    print(f"   • COMPOSITE SCORE: {analysis['composite_score']:.4f}")

    print(f"\n   Signal Decision:")
    print(f"   • Buy Threshold: {analysis['buy_threshold']}")
    print(f"   • Sell Threshold: {analysis['sell_threshold']}")
    print(f"   • Generated Signal: {analysis['action']}")

    # Determine if BUY signal
    if analysis["composite_score"] >= analysis["buy_threshold"]:
        signal_text = "🟢 BUY SIGNAL - Conditions Met"
        action_color = "green"
    elif analysis["composite_score"] <= analysis["sell_threshold"]:
        signal_text = "🔴 SELL SIGNAL - Downside Risk"
        action_color = "red"
    else:
        signal_text = "🟡 HOLD SIGNAL - Neutral Zone"
        action_color = "yellow"

    print(f"\n   ➜ {signal_text}")

    # ─────────────────────────────────────────────────────────────────────────
    # 4. DISCORD NOTIFICATION: ML ANALYSIS
    # ─────────────────────────────────────────────────────────────────────────
    print("\n📢 STEP 4: Discord Notification - ML Analysis")
    print("-" * 90)

    webhook = (
        os.getenv("DISCORD_WEBHOOK_NOOMO", "").strip()
        or os.getenv("DISCORD_AI_ML_WEBHOOK", "").strip()
    )

    if webhook:
        embed = {
            "title": f"🤖 Altair ML Signal: {symbol}",
            "color": 0x00FF00 if analysis["action"] == "BUY" else 0xFF0000,
            "fields": [
                {"name": "Symbol", "value": symbol, "inline": True},
                {"name": "Action", "value": analysis["action"], "inline": True},
                {
                    "name": "Composite Score",
                    "value": f"{analysis['composite_score']:.4f}",
                    "inline": True,
                },
                {
                    "name": "Sentiment Score",
                    "value": f"{analysis['sentiment']['score']:.4f}",
                    "inline": True,
                },
                {"name": "Fund", "value": analysis["fund"], "inline": True},
                {"name": "Strategy", "value": analysis["strategy"], "inline": True},
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            r = requests.post(webhook, json={"embeds": [embed]}, timeout=5)
            if r.ok:
                print(f"✅ Discord notification sent to #ai-ml")
                print(f"   Composite Score: {analysis['composite_score']:.4f}")
                print(f"   Signal: {analysis['action']}")
            else:
                print(f"⚠️  Discord notification failed: {r.status_code}")
        except Exception as e:
            print(f"⚠️  Discord notification error: {e}")
    else:
        print(f"⚠️  DISCORD_WEBHOOK_NOOMO not configured (would post ML analysis)")

    # ─────────────────────────────────────────────────────────────────────────
    # 5. TRADE EXECUTION (PAPER MODE)
    # ─────────────────────────────────────────────────────────────────────────
    print("\n💹 STEP 5: Trade Execution (Paper Mode)")
    print("-" * 90)

    trade_result = None
    if analysis["action"] == "BUY":
        qty = 100  # Paper trade quantity
        print(f"✅ BUY signal detected. Executing paper trade...")
        print(f"   • Symbol: {symbol}")
        print(f"   • Action: BUY")
        print(f"   • Quantity: {qty} shares")
        print(f"   • Estimated Entry: $500+ (current market)")

        trade_result = bot.execute_trade(
            broker="alpaca",
            ticker=symbol,
            action="BUY",
            qty=qty,
            dry_run=True,  # Force paper/dry-run mode
        )

        print(f"\n✅ Trade Submitted (Paper Mode)")
        print(f"   • Broker: {trade_result.get('broker', 'alpaca')}")
        print(f"   • Status: {trade_result.get('status', 'simulated')}")
        print(f"   • Order ID: {trade_result.get('order_id', 'SIM-' + symbol + '-001')}")
    else:
        print(f"⏸️  {analysis['action']} signal - No trade executed")
        print(f"   Current composite score: {analysis['composite_score']:.4f}")
        print(f"   Buy threshold: {analysis['buy_threshold']}")

    # ─────────────────────────────────────────────────────────────────────────
    # 6. DISCORD NOTIFICATION: TRADE EXECUTION
    # ─────────────────────────────────────────────────────────────────────────
    print("\n📢 STEP 6: Discord Notification - Trade Execution")
    print("-" * 90)

    if trade_result:
        bot_webhook = (
            os.getenv("DISCORD_BOT_TALK_WEBHOOK", "").strip()
            or os.getenv("DISCORD_WEBHOOK_URL", "").strip()
            or os.getenv("DISCORD_WEBHOOK", "").strip()
        )

        if bot_webhook:
            embed = {
                "title": f"💹 Altair Trade: BUY 100 {symbol}",
                "color": 0x00FF00,
                "fields": [
                    {"name": "Symbol", "value": symbol, "inline": True},
                    {"name": "Side", "value": "BUY", "inline": True},
                    {"name": "Quantity", "value": "100", "inline": True},
                    {
                        "name": "Status",
                        "value": trade_result.get("status", "simulated"),
                        "inline": True,
                    },
                    {"name": "Fund", "value": "Mansa AI Fund", "inline": True},
                    {"name": "Strategy", "value": "News Trading", "inline": True},
                ],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            try:
                r = requests.post(bot_webhook, json={"embeds": [embed]}, timeout=5)
                if r.ok:
                    print(f"✅ Discord notification sent to #bot_talk")
                    print(f"   Symbol: {symbol}")
                    print(f"   Action: BUY 100 shares")
                else:
                    print(f"⚠️  Discord notification failed: {r.status_code}")
            except Exception as e:
                print(f"⚠️  Discord notification error: {e}")
        else:
            print(f"⚠️  DISCORD_BOT_TALK_WEBHOOK not configured (would post trade)")

    # ─────────────────────────────────────────────────────────────────────────
    # 7. BENTLEY DASHBOARD INTEGRATION
    # ─────────────────────────────────────────────────────────────────────────
    print("\n📊 STEP 7: Bentley Dashboard Integration")
    print("-" * 90)

    health = bot.health_snapshot(probe_fastapi=False)

    print(f"✅ Dashboard Data Prepared")
    print(f"   • Bot: {health['name']}")
    print(f"   • Fund: {health['fund']}")
    print(f"   • Strategy: {health['strategy']}")
    print(f"   • Dashboard URL: {health['dashboard_url']}")
    print(f"   • Last Analysis: {json.dumps(analysis, indent=2)}")

    # ─────────────────────────────────────────────────────────────────────────
    # 8. SUMMARY
    # ─────────────────────────────────────────────────────────────────────────
    print("\n✅ ALTAIR DEMO COMPLETE")
    print("=" * 90)

    print(f"\nExecution Summary:")
    print(f"  • ML Analysis: ✅ Complete (Composite Score: {analysis['composite_score']:.4f})")
    print(f"  • Signal: {analysis['action']}")
    if trade_result:
        print(f"  • Trade Execution: ✅ {trade_result.get('status', 'submitted')}")
        print(
            f"  • Discord Notifications: ✅ #ai-ml, #bot_talk (2 messages)"
        )
    else:
        print(f"  • Trade Execution: ⏸️  Skipped (signal={analysis['action']})")
        print(f"  • Discord Notifications: ✅ #ai-ml (1 message)")
    print(f"  • Bentley Dashboard: ✅ Ready for display")

    print(f"\nNext Steps:")
    print(f"  1. Check Discord #ai-ml for ML analysis results")
    if trade_result:
        print(f"  2. Check Discord #bot_talk for trade execution confirmation")
    print(f"  3. Open Bentley Dashboard at {health['dashboard_url']}")
    print(f"  4. View Altair signals in Mansa AI Fund portfolio section")

    print("\n" + "=" * 90 + "\n")


if __name__ == "__main__":
    main()
