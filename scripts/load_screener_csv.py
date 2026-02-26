from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml


DEFAULT_CONFIG_PATH = Path("config/fundamentals_bots.yml")
TICKER_COLUMNS = ("Ticker", "Symbol", "ticker", "symbol")

FUNDAMENTALS_COLUMN_MAP = {
    "volume": ("volume", "avg_volume", "avgVolume", "Volume"),
    "pe": ("pe", "pe_ratio", "P/E", "peRatio"),
    "roe": ("roe", "return_on_equity", "ROE", "returnOnEquity"),
    "debt_to_equity": (
        "debt_to_equity",
        "debtToEquity",
        "de_ratio",
        "D/E",
    ),
    "dividend_yield": (
        "dividend_yield",
        "dividendYield",
        "div_yield",
        "Dividend Yield",
    ),
}


def load_bot_config(bot_name: str, config_path: Path | str = DEFAULT_CONFIG_PATH) -> Dict:
    config_file = Path(config_path)
    with config_file.open("r", encoding="utf-8") as file_handle:
        config = yaml.safe_load(file_handle) or {}

    bots = config.get("bots")
    if not isinstance(bots, dict):
        raise ValueError(f"Invalid config format in {config_file}: missing 'bots' mapping")

    if bot_name not in bots:
        available = ", ".join(sorted(bots.keys()))
        raise ValueError(
            f"Bot '{bot_name}' not found in {config_file}. Available bots: {available}"
        )

    bot_cfg = bots[bot_name]
    if not isinstance(bot_cfg, dict):
        raise ValueError(f"Bot '{bot_name}' config must be a mapping")

    return bot_cfg


def _candidate_screener_paths(screener_file: str, config_file: Path) -> Iterable[Path]:
    screener_path = Path(screener_file)
    if screener_path.is_absolute():
        yield screener_path
        return

    yield config_file.parent / screener_file
    yield config_file.parent.parent / screener_file
    yield config_file.parent.parent / "data" / screener_file


def resolve_screener_path(
    bot_config: Dict, config_path: Path | str = DEFAULT_CONFIG_PATH
) -> Path:
    config_file = Path(config_path)
    screener_file = str(bot_config.get("screener_file", "")).strip()
    if not screener_file:
        raise ValueError("Bot config is missing 'screener_file'")

    attempted: List[Path] = []
    for candidate in _candidate_screener_paths(screener_file, config_file):
        attempted.append(candidate)
        if candidate.exists():
            return candidate

    attempts = "\n - ".join(str(path) for path in attempted)
    raise FileNotFoundError(
        "Screener CSV not found for bot. Tried:\n"
        f" - {attempts}"
    )


def load_screener_csv(csv_path: Path | str) -> List[str]:
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV not found: {csv_file}")

    tickers: List[str] = []
    with csv_file.open("r", encoding="utf-8-sig", newline="") as file_handle:
        reader = csv.DictReader(file_handle)
        for row in reader:
            ticker_value: Optional[str] = None
            for key in TICKER_COLUMNS:
                value = row.get(key)
                if value:
                    ticker_value = value
                    break

            if ticker_value:
                normalized = ticker_value.strip().upper()
                if normalized:
                    tickers.append(normalized)

    return sorted(set(tickers))


def load_screener_rows(csv_path: Path | str) -> List[Dict[str, str]]:
    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV not found: {csv_file}")

    rows: List[Dict[str, str]] = []
    with csv_file.open("r", encoding="utf-8-sig", newline="") as file_handle:
        reader = csv.DictReader(file_handle)
        for row in reader:
            rows.append(dict(row))
    return rows


def _to_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _pick_first_value(row: Dict[str, str], aliases: Iterable[str]) -> Optional[str]:
    for key in aliases:
        value = row.get(key)
        if value is not None and str(value).strip() != "":
            return str(value)
    return None


def _extract_symbol(row: Dict[str, str]) -> Optional[str]:
    symbol = _pick_first_value(row, TICKER_COLUMNS)
    if symbol is None:
        return None
    normalized = symbol.strip().upper()
    return normalized or None


def _extract_fundamentals(row: Dict[str, str]) -> Dict[str, float]:
    fundamentals: Dict[str, float] = {}
    for normalized_key, aliases in FUNDAMENTALS_COLUMN_MAP.items():
        raw_value = _pick_first_value(row, aliases)
        numeric_value = _to_float(raw_value)
        if numeric_value is not None:
            fundamentals[normalized_key] = numeric_value
    return fundamentals


def load_bot_trade_candidates(
    bot_name: str,
    config_path: Path | str = DEFAULT_CONFIG_PATH,
) -> List[Dict[str, Any]]:
    bot_cfg = load_bot_config(bot_name, config_path=config_path)
    screener_csv = resolve_screener_path(bot_cfg, config_path=config_path)
    rows = load_screener_rows(screener_csv)

    candidates: List[Dict[str, Any]] = []
    for row in rows:
        symbol = _extract_symbol(row)
        if not symbol:
            continue

        candidates.append(
            {
                "symbol": symbol,
                "fundamentals": _extract_fundamentals(row),
                "raw": row,
            }
        )

    deduped: List[Dict[str, Any]] = []
    seen_symbols = set()
    for candidate in candidates:
        symbol = candidate["symbol"]
        if symbol in seen_symbols:
            continue
        seen_symbols.add(symbol)
        deduped.append(candidate)
    return deduped


def load_bot_tickers(
    bot_name: str, config_path: Path | str = DEFAULT_CONFIG_PATH
) -> List[str]:
    bot_cfg = load_bot_config(bot_name, config_path=config_path)
    screener_csv = resolve_screener_path(bot_cfg, config_path=config_path)
    return load_screener_csv(screener_csv)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load Titan/Vega (or any configured bot) tickers from screener CSV"
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to bot config YAML (default: config/fundamentals_bots.yml)",
    )
    parser.add_argument(
        "--bots",
        nargs="+",
        default=["Titan_Bot", "Vega_Bot"],
        help="Bot names to load tickers for",
    )
    args = parser.parse_args()

    has_errors = False
    for bot_name in args.bots:
        try:
            bot_cfg = load_bot_config(bot_name, config_path=args.config)
            screener_csv = resolve_screener_path(bot_cfg, config_path=args.config)
            tickers = load_screener_csv(screener_csv)
            print(f"{bot_name} ({screener_csv}): {len(tickers)} tickers")
            print(tickers)
        except (FileNotFoundError, ValueError) as exc:
            has_errors = True
            print(f"{bot_name}: {exc}")

    if has_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
