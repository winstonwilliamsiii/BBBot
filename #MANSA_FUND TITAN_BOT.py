"""
Compatibility entrypoint for Mansa Fund Titan Bot.

Primary implementation is in scripts/mansa_titan_bot.py.
"""

import argparse

from scripts.mansa_titan_bot import TitanBot, TitanConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Mansa Titan/Vega fundamentals bot")
    parser.add_argument(
        "--from-screener",
        action="store_true",
        help="Execute screener-driven trades (uses bot_cfg screener_file + risk_rules)",
    )
    parser.add_argument(
        "--max-trades",
        type=int,
        default=0,
        help="Maximum screener symbols to process (0 = all)",
    )
    args = parser.parse_args()

    bot = TitanBot(TitanConfig.from_env())
    bot.ensure_database_tables()
    if args.from_screener:
        limit = args.max_trades if args.max_trades > 0 else None
        results = bot.execute_from_screener(max_trades=limit)
        print(
            f"Processed {len(results)} screener symbols for {bot.config.active_bot_name}."
        )
    print("Mansa Tech - Titan Bot initialized.")


if __name__ == "__main__":
    main()

