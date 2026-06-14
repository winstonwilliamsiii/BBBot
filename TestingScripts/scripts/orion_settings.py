from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ORION_CONFIG_PATH = (
    PROJECT_ROOT / "bentley-bot" / "config" / "bots" / "orion.yml"
)


@dataclass(frozen=True)
class OrionSettings:
    bot_name: str
    fund_name: str
    strategy_label: str
    primary_client: str
    execution_venue: str
    execution_mode: str
    execution_enabled: bool
    order_type: str
    volume_lots: float
    close_on_reverse: bool
    stop_loss_pct: float
    take_profit_pct: float
    symbol_map: Dict[str, str]
    primary_symbol: str
    training_symbol: str
    scan_symbols: List[str]
    scan_top_n: int
    screener_file: str
    timeframe: str
    universe: str
    position_size: float
    rsi_period: int
    rsi_oversold: float
    rsi_overbought: float


def _normalize_symbol(value: str) -> str:
    return str(value or "").strip().upper()


def _read_orion_config(config_path: Path) -> Dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid Orion config format in {config_path}")
    return data


def _resolve_screener_path(config_path: Path, screener_file: str) -> Path:
    candidate = Path(screener_file)
    if candidate.is_absolute() and candidate.exists():
        return candidate

    search_paths = [
        config_path.parent.parent / screener_file,
        PROJECT_ROOT / "bentley-bot" / "config" / screener_file,
        PROJECT_ROOT / "config" / screener_file,
    ]
    for path in search_paths:
        if path.exists():
            return path
    raise FileNotFoundError(f"Orion screener file not found: {screener_file}")


def _load_scan_symbols(screener_path: Path) -> List[str]:
    symbols: List[str] = []
    with screener_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            symbol = _normalize_symbol(
                row.get("Symbol")
                or row.get("symbol")
                or row.get("Ticker")
                or row.get("ticker")
                or ""
            )
            if symbol:
                symbols.append(symbol)

    deduped: List[str] = []
    seen = set()
    for symbol in symbols:
        if symbol in seen:
            continue
        seen.add(symbol)
        deduped.append(symbol)
    return deduped


def load_orion_settings(config_path: Path | None = None) -> OrionSettings:
    resolved_config = config_path or ORION_CONFIG_PATH
    data = _read_orion_config(resolved_config)

    bot_data = data.get("bot")
    bot_meta: Dict[str, Any] = bot_data if isinstance(bot_data, dict) else {}
    strategy_data = data.get("strategy")
    strategy_meta: Dict[str, Any] = (
        strategy_data if isinstance(strategy_data, dict) else {}
    )
    execution_data = data.get("execution")
    execution_meta: Dict[str, Any] = (
        execution_data if isinstance(execution_data, dict) else {}
    )
    risk_data = data.get("risk")
    risk_meta: Dict[str, Any] = (
        risk_data if isinstance(risk_data, dict) else {}
    )

    screener_file = str(
        strategy_meta.get("screener_file") or "orion_minerals_fundamentals.csv"
    )
    screener_path = _resolve_screener_path(resolved_config, screener_file)

    configured_symbols = strategy_meta.get("scan_symbols")
    scan_symbols = [
        _normalize_symbol(symbol)
        for symbol in configured_symbols
        if _normalize_symbol(symbol)
    ] if isinstance(configured_symbols, list) else []
    if not scan_symbols:
        scan_symbols = _load_scan_symbols(screener_path)

    primary_symbol = _normalize_symbol(
        strategy_meta.get("primary_symbol") or "GDX"
    ) or "GDX"
    training_symbol = _normalize_symbol(
        strategy_meta.get("training_symbol") or primary_symbol
    ) or primary_symbol

    if primary_symbol not in scan_symbols:
        scan_symbols.insert(0, primary_symbol)

    return OrionSettings(
        bot_name=str(bot_meta.get("name") or "Orion"),
        fund_name="Mansa_Minerals",
        strategy_label=str(
            strategy_meta.get("label") or "Orion_Minerals_RSI_Scanner"
        ),
        primary_client=str(
            execution_meta.get("primary_client") or "mt5_client"
        ),
        execution_venue=str(execution_meta.get("venue") or "ftmo"),
        execution_mode=str(execution_meta.get("mode") or "paper"),
        execution_enabled=bool(execution_meta.get("enabled", False)),
        order_type=str(execution_meta.get("order_type") or "market"),
        volume_lots=float(execution_meta.get("volume_lots") or 0.01),
        close_on_reverse=bool(execution_meta.get("close_on_reverse", True)),
        stop_loss_pct=float(execution_meta.get("stop_loss_pct") or 0.015),
        take_profit_pct=float(execution_meta.get("take_profit_pct") or 0.03),
        symbol_map={
            _normalize_symbol(key): _normalize_symbol(value)
            for key, value in (execution_meta.get("symbol_map") or {}).items()
            if _normalize_symbol(key) and _normalize_symbol(value)
        },
        primary_symbol=primary_symbol,
        training_symbol=training_symbol,
        scan_symbols=scan_symbols,
        scan_top_n=max(int(strategy_meta.get("scan_top_n") or 3), 1),
        screener_file=screener_file,
        timeframe=str(strategy_meta.get("timeframe") or "1D"),
        universe=str(strategy_meta.get("universe") or "Minerals_Commodities"),
        position_size=float(strategy_meta.get("position_size") or 2200),
        rsi_period=max(int(risk_meta.get("rsi_period") or 14), 2),
        rsi_oversold=float(risk_meta.get("rsi_oversold") or 30),
        rsi_overbought=float(risk_meta.get("rsi_overbought") or 70),
    )
