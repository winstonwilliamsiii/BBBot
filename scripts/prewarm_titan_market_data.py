from __future__ import annotations

import argparse
import json
from typing import Iterable, List

try:
    from scripts.load_screener_csv import load_bot_trade_candidates
    from scripts.mansa_titan_bot import TitanBot, TitanConfig
except ModuleNotFoundError:
    from load_screener_csv import load_bot_trade_candidates
    from mansa_titan_bot import TitanBot, TitanConfig


def _resolve_symbols(explicit_symbols: Iterable[str] | None) -> List[str]:
    if explicit_symbols:
        return sorted(
            {
                symbol.strip().upper()
                for symbol in explicit_symbols
                if symbol and symbol.strip()
            }
        )

    config = TitanConfig.from_env()
    candidates = load_bot_trade_candidates(config.active_bot_name)
    return sorted(
        {
            str(candidate.get("symbol", "")).strip().upper()
            for candidate in candidates
            if str(candidate.get("symbol", "")).strip()
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prewarm Titan market-data and account caches.",
    )
    parser.add_argument(
        "symbols",
        nargs="*",
        help="Optional explicit symbols to prewarm.",
    )
    args = parser.parse_args()

    bot = TitanBot(TitanConfig.from_env())
    snapshot = bot.get_account_snapshot()
    symbols = _resolve_symbols(args.symbols)
    warmed = []
    for symbol in symbols:
        feature_payload = bot._build_prediction_features(symbol, [])
        metadata = bot._last_prediction_feature_metadata.get(symbol, {})
        warmed.append(
            {
                "symbol": symbol,
                "market_data_source": bot._last_market_data_source.get(
                    symbol,
                    "unknown",
                ),
                "close_history_points": int(
                    metadata.get("close_history_points", 0)
                ),
                "cache_ready": bool(
                    metadata.get("close_history_points", 0) > 0
                ),
                "feature_payload_type": type(feature_payload).__name__,
                "feature_metadata": metadata,
            }
        )

    print(
        json.dumps(
            {
                "account_snapshot": snapshot,
                "symbols_requested": symbols,
                "symbols_warmed": warmed,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
