from __future__ import annotations

from bentley_bot.bots.vega_bot import *  # noqa: F401,F403

if __name__ == "__main__":
    import runpy

    runpy.run_module("bentley_bot.bots.vega_bot", run_name="__main__")
