from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml


SCAFFOLD_PROFILE_DIR = Path("bentley-bot/config/bots")
LEGACY_CONFIG_PATH = Path("config/fundamentals_bots.yml")
DEFAULT_CONFIG_PATH = SCAFFOLD_PROFILE_DIR
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


def _normalize_bot_name(bot_name: str) -> str:
    return str(bot_name or "").strip()


def _bot_slug(bot_name: str) -> str:
    normalized = _normalize_bot_name(bot_name)
    lowered = normalized.lower()
    if lowered.endswith("_bot"):
        lowered = lowered[:-4]
    return lowered.replace(" ", "_")


def _read_yaml_file(config_file: Path) -> Dict[str, Any]:
    with config_file.open("r", encoding="utf-8") as file_handle:
        data = yaml.safe_load(file_handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid config format in {config_file}: expected YAML mapping")
    return data


def _load_aggregate_bot_config(bot_name: str, config_file: Path) -> Dict[str, Any]:
    config = _read_yaml_file(config_file)
    bots = config.get("bots")
    if not isinstance(bots, dict):
        raise ValueError(f"Invalid config format in {config_file}: missing 'bots' mapping")

    normalized_name = _normalize_bot_name(bot_name)
    if not normalized_name:
        normalized_name = str(config.get("active_bot") or "")

    candidate_names = [normalized_name] if normalized_name else []
    if normalized_name and not normalized_name.lower().endswith("_bot"):
        candidate_names.append(f"{normalized_name}_Bot")

    bot_cfg: Optional[Dict[str, Any]] = None
    resolved_name: Optional[str] = None
    for candidate in candidate_names:
        maybe_cfg = bots.get(candidate)
        if isinstance(maybe_cfg, dict):
            bot_cfg = maybe_cfg
            resolved_name = candidate
            break

    if bot_cfg is None:
        available = ", ".join(sorted(bots.keys()))
        raise ValueError(
            f"Bot '{bot_name}' not found in {config_file}. Available bots: {available}"
        )

    return {
        **bot_cfg,
        "bot_name": resolved_name or normalized_name,
    }


def _normalize_single_bot_profile(bot_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    bot_meta = data.get("bot") if isinstance(data.get("bot"), dict) else {}
    strategy_meta = (
        data.get("strategy") if isinstance(data.get("strategy"), dict) else {}
    )
    execution_meta = (
        data.get("execution") if isinstance(data.get("execution"), dict) else {}
    )
    risk_meta = data.get("risk") if isinstance(data.get("risk"), dict) else {}

    display_name = str(bot_meta.get("name") or _normalize_bot_name(bot_name) or "Titan")
    runtime_name = str(bot_meta.get("runtime_name") or display_name)
    if runtime_name and not runtime_name.lower().endswith("_bot"):
        runtime_name = f"{runtime_name}_Bot"

    position_size = strategy_meta.get("position_size")
    if position_size in (None, ""):
        position_size = 0

    return {
        "bot_name": runtime_name,
        "bot_display_name": display_name,
        "fund_name": str(bot_meta.get("fund") or ""),
        "strategy_label": str(
            strategy_meta.get("label") or bot_meta.get("strategy") or ""
        ),
        "strategy_name": str(bot_meta.get("strategy") or ""),
        "module": str(bot_meta.get("module") or ""),
        "screener_file": str(strategy_meta.get("screener_file") or ""),
        "universe": str(strategy_meta.get("universe") or ""),
        "timeframe": str(strategy_meta.get("timeframe") or ""),
        "position_size": position_size,
        "risk_rules": dict(risk_meta),
        "execution": dict(execution_meta),
    }


def _resolve_single_profile_path(bot_name: str, config_path: Path) -> Path:
    if config_path.is_file():
        return config_path

    if not config_path.exists() and config_path == DEFAULT_CONFIG_PATH:
        if LEGACY_CONFIG_PATH.exists():
            return LEGACY_CONFIG_PATH

    if config_path.is_dir():
        candidate = config_path / f"{_bot_slug(bot_name)}.yml"
        if candidate.exists():
            return candidate
        raise ValueError(f"Bot profile file not found for '{bot_name}' in {config_path}")

    raise FileNotFoundError(f"Bot config path not found: {config_path}")


def load_bot_config(bot_name: str, config_path: Path | str = DEFAULT_CONFIG_PATH) -> Dict:
    config_file = Path(config_path)

    if config_file == DEFAULT_CONFIG_PATH and not config_file.exists():
        config_file = LEGACY_CONFIG_PATH

    if config_file.is_file():
        config = _read_yaml_file(config_file)
        if "bots" in config:
            return _load_aggregate_bot_config(bot_name, config_file)
        return _normalize_single_bot_profile(bot_name, config)

    if config_file.is_dir() or config_file == DEFAULT_CONFIG_PATH:
        profile_path = _resolve_single_profile_path(bot_name, config_file)
        return _normalize_single_bot_profile(bot_name, _read_yaml_file(profile_path))

    raise FileNotFoundError(f"Bot config path not found: {config_file}")


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
