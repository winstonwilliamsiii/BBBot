"""
Compatibility entrypoint for Mansa Fund Titan Bot.

Primary implementation is in scripts/mansa_titan_bot.py.
"""

from scripts.mansa_titan_bot import TitanBot, TitanConfig


def main() -> None:
    bot = TitanBot(TitanConfig.from_env())
    bot.ensure_database_tables()
    print("Mansa Tech - Titan Bot initialized.")


if __name__ == "__main__":
    main()

