"""Legacy Triton scratch file retained as a wrapper to the runtime module."""

from triton_bot import TritonBot


if __name__ == "__main__":
    bot = TritonBot()
    print(bot.bootstrap_demo_state())