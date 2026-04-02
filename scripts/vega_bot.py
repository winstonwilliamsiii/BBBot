"""Dedicated Vega_Bot entrypoint for the Mansa_Retail fund runtime."""

from __future__ import annotations

import argparse
import os

from scripts.mansa_titan_bot import TitanBot, TitanConfig


DEFAULT_ACTIVE_BOT = "Vega_Bot"
DEFAULT_STRATEGY_NAME = "Vega Mansa Retail MTF-ML"


def _configure_runtime_env() -> None:
    os.environ.setdefault("ACTIVE_BOT", DEFAULT_ACTIVE_BOT)
    os.environ.setdefault("BOT_NAME", DEFAULT_ACTIVE_BOT)
    os.environ.setdefault("TITAN_STRATEGY_NAME", DEFAULT_STRATEGY_NAME)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Vega_Bot for the Mansa_Retail fund"
    )
    parser.add_argument(
        "--init-only",
        action="store_true",
        help="Initialize the Vega runtime without executing screener trades",
    )
    parser.add_argument(
        "--max-trades",
        type=int,
        default=1,
        help="Maximum screener symbols to process (0 = all)",
    )
    parser.add_argument(
        "--side",
        default="buy",
        choices=["buy", "sell"],
        help="Order side to pass through to screener execution",
    )
    args = parser.parse_args()

    _configure_runtime_env()

    bot = TitanBot(TitanConfig.from_env())
    bot.ensure_database_tables()

    if args.init_only:
        print("Vega_Bot initialized successfully.")
        return

    limit = args.max_trades if args.max_trades > 0 else None
    results = bot.execute_from_screener(side=args.side, max_trades=limit)
    print(
        f"Processed {len(results)} screener symbols for {bot.config.active_bot_name}."
    )


if __name__ == "__main__":
    main()