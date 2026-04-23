"""
IBKR Market Data Stub — Intraday & Swing Strategy Feed
─────────────────────────────────────────────────────────────────────────────
Wraps frontend.components.ibkr_connector.IBKRConnector to provide
strategy-ready bar data for intraday and swing endpoints.

Bot strategy map
~~~~~~~~~~~~~~~~
  Rhea_Bot  — Intra-Day AND Swing  (ADI divergence, 30-min bars, ADI universe)
  Triton_Bot — Swing ONLY          (ARIMA + LSTM, 1-day bars, Transport universe)

Gateway must be running locally (default https://localhost:5000).
When the gateway is unreachable the stub returns synthetic placeholder
bars so strategy endpoints stay functional in dev/paper environments.

Usage:
    from frontend.utils.ibkr_market_data import IBKRMarketDataStub, for_bot

    # --- Generic ---
    stub = IBKRMarketDataStub()
    bars = stub.get_intraday_bars("AAPL")     # 5-min bars, 1-day lookback
    bars = stub.get_swing_bars("AAPL")        # 30-min bars, 10-day lookback
    snap = stub.get_snapshot("AAPL")          # live bid/ask/last

    # --- Bot-specific presets (recommended) ---
    rhea   = for_bot("Rhea_Bot")              # intraday + swing, 5-min / 30-min
    triton = for_bot("Triton_Bot")            # swing only, 1-day bars, 1-year period

    bars   = triton.get_swing_bars("UNP")
    payload = rhea.strategy_intraday_payload("LMT")

    # --- Drive entirely from bots_config.yaml ---
    from frontend.utils.bot_config_loader import load_bot_config
    cfg  = load_bot_config("Rhea_Bot")
    stub = IBKRMarketDataStub.from_bot_config(cfg)
─────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Field IDs used for IBKR snapshot requests (Client Portal API).
_FIELD_LAST = 31
_FIELD_BID = 84
_FIELD_ASK = 85
_FIELD_VOLUME = 86
_FIELD_CHANGE = 88

_DEFAULT_SNAPSHOT_FIELDS = [
    _FIELD_LAST, _FIELD_BID, _FIELD_ASK, _FIELD_VOLUME, _FIELD_CHANGE
]


@dataclass
class OHLCVBar:
    """Single OHLCV bar returned by the market data stub."""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str = "ibkr"


@dataclass
class MarketSnapshot:
    """Real-time quote snapshot."""
    symbol: str
    conid: int | None
    last: float | None
    bid: float | None
    ask: float | None
    volume: float | None
    change: float | None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source: str = "ibkr"


class IBKRMarketDataStub:
    """
    Strategy-level IBKR market data provider.

    Parameters
    ----------
    gateway_url:
        IBKR Client Portal Gateway base URL.
    intraday_bar:
        Bar size for intraday strategy feed (``"1min"``, ``"5min"``).
    swing_bar:
        Bar size for swing strategy feed (``"30min"``, ``"1h"``).
    intraday_period:
        Lookback period for intraday bars (``"1d"``, ``"2d"``).
    swing_period:
        Lookback period for swing bars (``"1w"``, ``"2w"``).
    snapshot_fields:
        IBKR market data field IDs to request in snapshots.
    """

    def __init__(
        self,
        gateway_url: str = "https://localhost:5000",
        intraday_bar: str = "5min",
        swing_bar: str = "30min",
        intraday_period: str = "1d",
        swing_period: str = "1w",
        snapshot_fields: list[int] | None = None,
        bot_key: str = "",
        supports: list[str] | None = None,
        universe: list[str] | None = None,
    ) -> None:
        self.gateway_url = gateway_url
        self.intraday_bar = intraday_bar
        self.swing_bar = swing_bar
        self.intraday_period = intraday_period
        self.swing_period = swing_period
        self.snapshot_fields = snapshot_fields or _DEFAULT_SNAPSHOT_FIELDS
        self.bot_key = bot_key
        self.supports = supports or ["intraday", "swing"]
        self.universe = universe or []
        self._connector: Any | None = None

    # ── Factory ────────────────────────────────────────────────────────────

    @classmethod
    def from_bot_config(cls, bot_cfg: dict[str, Any]) -> "IBKRMarketDataStub":
        """
        Construct from a bot config dict produced by bot_config_loader.

        Only ``market_data.provider == "ibkr"`` bots use IBKR; other providers
        still get a stub instance but calls will be transparently delegated
        (or will return placeholders if not wired yet).
        """
        md = bot_cfg.get("market_data", {})
        return cls(
            gateway_url=md.get("ibkr_gateway_url", "https://localhost:5000"),
            intraday_bar=md.get("intraday_bar", "5min"),
            swing_bar=md.get("swing_bar", "30min"),
            intraday_period=md.get("intraday_period", "1d"),
            swing_period=md.get("swing_period", "1w"),
            snapshot_fields=md.get("snapshot_fields", _DEFAULT_SNAPSHOT_FIELDS),
        )

    # ── Internal helpers ────────────────────────────────────────────────────

    def _connector_instance(self) -> Any:
        """Lazy-init IBKRConnector; returns None if gateway unavailable."""
        if self._connector is not None:
            return self._connector
        try:
            from frontend.components.ibkr_connector import IBKRConnector
            conn = IBKRConnector(base_url=self.gateway_url, verify_ssl=False)
            if conn.is_authenticated():
                self._connector = conn
                logger.info("IBKR gateway connected: %s", self.gateway_url)
            else:
                logger.warning(
                    "IBKR gateway reachable but not authenticated (%s). "
                    "Returning stub placeholders.",
                    self.gateway_url,
                )
        except Exception as exc:
            logger.warning("IBKR gateway unavailable (%s): %s — using stub data.", self.gateway_url, exc)
        return self._connector

    def _resolve_conid(self, symbol: str) -> int | None:
        """Look up a contract ID via the gateway; returns None on failure."""
        conn = self._connector_instance()
        if conn is None:
            return None
        try:
            results = conn.search_contract(symbol)
            if results:
                return results[0].get("conid")
        except Exception as exc:
            logger.warning("conid lookup failed for %s: %s", symbol, exc)
        return None

    @staticmethod
    def _stub_bars(count: int = 10) -> list[OHLCVBar]:
        """Return synthetic OHLCV bars when gateway is unreachable."""
        import random

        base_price = 150.0
        bars: list[OHLCVBar] = []
        for i in range(count):
            noise = random.uniform(-2.0, 2.0)
            o = round(base_price + noise, 2)
            c = round(o + random.uniform(-1.5, 1.5), 2)
            h = round(max(o, c) + random.uniform(0.1, 1.0), 2)
            lo = round(min(o, c) - random.uniform(0.1, 1.0), 2)
            vol = round(random.uniform(50_000, 500_000), 0)
            bars.append(
                OHLCVBar(
                    timestamp=f"stub_bar_{i}",
                    open=o,
                    high=h,
                    low=lo,
                    close=c,
                    volume=vol,
                    source="stub",
                )
            )
            base_price = c
        return bars

    @staticmethod
    def _parse_bars(raw: dict[str, Any], source: str = "ibkr") -> list[OHLCVBar]:
        """Convert IBKR /marketdata/history response to OHLCVBar list."""
        bars: list[OHLCVBar] = []
        for item in raw.get("data", []):
            bars.append(
                OHLCVBar(
                    timestamp=item.get("t", ""),
                    open=float(item.get("o", 0)),
                    high=float(item.get("h", 0)),
                    low=float(item.get("l", 0)),
                    close=float(item.get("c", 0)),
                    volume=float(item.get("v", 0)),
                    source=source,
                )
            )
        return bars

    # ── Public API ──────────────────────────────────────────────────────────

    def get_intraday_bars(
        self,
        symbol: str,
        period: str | None = None,
        bar: str | None = None,
    ) -> list[OHLCVBar]:
        """
        Fetch intraday OHLCV bars for *symbol*.

        Falls back to synthetic stub bars when the gateway is unavailable
        so intraday strategy endpoints can still return a response.

        Parameters
        ----------
        symbol:
            Ticker symbol (e.g. ``"AAPL"``).
        period:
            Override lookback period (default: ``self.intraday_period``).
        bar:
            Override bar size (default: ``self.intraday_bar``).
        """
        _period = period or self.intraday_period
        _bar = bar or self.intraday_bar

        conid = self._resolve_conid(symbol)
        if conid is None:
            logger.info("Using stub intraday bars for %s (no conid)", symbol)
            return self._stub_bars(count=78)  # ~6.5h / 5min

        conn = self._connector_instance()
        if conn is None:
            return self._stub_bars(count=78)

        try:
            raw = conn.get_historical_data(conid, period=_period, bar=_bar)
            if raw:
                return self._parse_bars(raw)
        except Exception as exc:
            logger.warning("Intraday bar fetch failed for %s: %s", symbol, exc)

        return self._stub_bars(count=78)

    def get_swing_bars(
        self,
        symbol: str,
        period: str | None = None,
        bar: str | None = None,
    ) -> list[OHLCVBar]:
        """
        Fetch swing-trade OHLCV bars for *symbol* (multi-day lookback).

        Falls back to synthetic stub bars when the gateway is unavailable.

        Parameters
        ----------
        symbol:
            Ticker symbol.
        period:
            Override lookback period (default: ``self.swing_period``).
        bar:
            Override bar size (default: ``self.swing_bar``).
        """
        _period = period or self.swing_period
        _bar = bar or self.swing_bar

        conid = self._resolve_conid(symbol)
        if conid is None:
            logger.info("Using stub swing bars for %s (no conid)", symbol)
            return self._stub_bars(count=50)

        conn = self._connector_instance()
        if conn is None:
            return self._stub_bars(count=50)

        try:
            raw = conn.get_historical_data(conid, period=_period, bar=_bar)
            if raw:
                return self._parse_bars(raw)
        except Exception as exc:
            logger.warning("Swing bar fetch failed for %s: %s", symbol, exc)

        return self._stub_bars(count=50)

    def get_snapshot(self, symbol: str) -> MarketSnapshot:
        """
        Fetch a real-time market snapshot (bid/ask/last/volume/change).

        Returns a stub snapshot when the gateway is unavailable.

        Parameters
        ----------
        symbol:
            Ticker symbol.
        """
        conid = self._resolve_conid(symbol)
        base = MarketSnapshot(
            symbol=symbol.upper(), conid=conid,
            last=None, bid=None, ask=None, volume=None, change=None,
        )

        if conid is None:
            base.source = "stub"
            return base

        conn = self._connector_instance()
        if conn is None:
            base.source = "stub"
            return base

        try:
            raw = conn.get_market_data([conid], fields=self.snapshot_fields)
            if raw and isinstance(raw, list) and len(raw) > 0:
                item = raw[0]
                base.last = _to_float(item.get(str(_FIELD_LAST)))
                base.bid = _to_float(item.get(str(_FIELD_BID)))
                base.ask = _to_float(item.get(str(_FIELD_ASK)))
                base.volume = _to_float(item.get(str(_FIELD_VOLUME)))
                base.change = _to_float(item.get(str(_FIELD_CHANGE)))
        except Exception as exc:
            logger.warning("Snapshot fetch failed for %s: %s", symbol, exc)
            base.source = "stub"

        return base

    def strategy_intraday_payload(self, symbol: str) -> dict[str, Any]:
        """
        Return a structured dict suitable for the /strategy/intraday endpoint.

        Shape mirrors what rhea_bot.py (and other bots) return from
        ``analyze_ticker`` so the response is consistent across data providers.
        """
        bars = self.get_intraday_bars(symbol)
        snap = self.get_snapshot(symbol)
        return {
            "symbol": symbol.upper(),
            "mode": "intraday",
            "bar_size": self.intraday_bar,
            "bar_count": len(bars),
            "latest_close": bars[-1].close if bars else None,
            "snapshot": {
                "last": snap.last,
                "bid": snap.bid,
                "ask": snap.ask,
                "volume": snap.volume,
                "change": snap.change,
            },
            "bars": [b.__dict__ for b in bars[-20:]],  # last 20 bars for payload
            "source": bars[0].source if bars else "stub",
        }

    def strategy_swing_payload(self, symbol: str) -> dict[str, Any]:
        """
        Return a structured dict suitable for the /strategy/swing endpoint.
        """
        bars = self.get_swing_bars(symbol)
        snap = self.get_snapshot(symbol)
        return {
            "symbol": symbol.upper(),
            "mode": "swing",
            "bar_size": self.swing_bar,
            "bar_count": len(bars),
            "latest_close": bars[-1].close if bars else None,
            "snapshot": {
                "last": snap.last,
                "bid": snap.bid,
                "ask": snap.ask,
                "volume": snap.volume,
                "change": snap.change,
            },
            "bars": [b.__dict__ for b in bars[-20:]],
            "source": bars[0].source if bars else "stub",
        }


def _to_float(val: Any) -> float | None:
    """Safely coerce a value to float, returning None on failure."""
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Bot-specific presets
# ─────────────────────────────────────────────────────────────────────────────

#: Hard-coded sensible defaults per bot, keyed by bot YAML key.
#: These are used by ``for_bot()`` when bots_config.yaml is unavailable.
_BOT_PRESETS: dict[str, dict[str, Any]] = {
    # ── Rhea — Intra-Day AND Swing ──────────────────────────────────────────
    # Strategy: ADI Divergence on 30-min bars, Aerospace/Defense/Industrials
    # Endpoints served: /strategy/intraday  +  /strategy/swing
    "Rhea_Bot": {
        "gateway_url":     "https://localhost:5000",
        "intraday_bar":    "5min",
        "swing_bar":       "30min",
        "intraday_period": "1d",
        "swing_period":    "1w",
        "snapshot_fields": [31, 84, 85, 86, 88],
        "supports": ["intraday", "swing"],
        "universe": [
            "LMT", "NOC", "RTX", "GD", "BA",
            "HII", "TXT", "CAT", "HON", "MMM",
        ],
    },
    # ── Triton — Swing ONLY ─────────────────────────────────────────────────
    # Strategy: ARIMA + LSTM on daily bars, Transportation universe
    # Endpoints served: /strategy/swing  (intraday returns swing bars as fallback)
    "Triton_Bot": {
        "gateway_url":     "https://localhost:5000",
        "intraday_bar":    "1h",       # Triton has no true intraday; use 1h as proxy
        "swing_bar":       "1d",
        "intraday_period": "5d",
        "swing_period":    "1y",
        "snapshot_fields": [31, 84, 85, 86, 88],
        "supports": ["swing"],         # declare only swing as primary strategy
        "universe": ["IYT", "UNP", "CSX", "NSC", "UPS", "FDX", "DAL", "UBER"],
    },
}


def for_bot(
    bot_key: str,
    config_path: str | None = None,
) -> "IBKRMarketDataStub":
    """
    Return an ``IBKRMarketDataStub`` pre-configured for the named bot.

    Preference order:
    1. ``config/bots_config.yaml`` ``market_data`` block (if loadable)
    2. ``_BOT_PRESETS`` hard-coded defaults above
    3. Generic defaults (``IBKRMarketDataStub()`` with no args)

    Parameters
    ----------
    bot_key:
        Bot name as used in bots_config.yaml, e.g. ``"Rhea_Bot"`` or
        ``"Triton_Bot"``.
    config_path:
        Optional override path to bots_config.yaml.

    Examples
    --------
    >>> rhea   = for_bot("Rhea_Bot")
    >>> triton = for_bot("Triton_Bot")
    >>> bars   = triton.get_swing_bars("UNP")
    >>> payload = rhea.strategy_intraday_payload("LMT")
    """
    # 1. Try YAML config first
    try:
        from frontend.utils.bot_config_loader import load_bot_config
        cfg = load_bot_config(bot_key, config_path=config_path)
        stub = IBKRMarketDataStub.from_bot_config(cfg)
        stub.bot_key = bot_key
        stub.supports = (
            cfg.get("market_data", {}).get("supports", ["intraday", "swing"])
        )
        stub.universe = cfg.get("universe", [])
        logger.info("for_bot(%s): loaded from bots_config.yaml", bot_key)
        return stub
    except Exception as exc:
        logger.debug("for_bot(%s): YAML load failed (%s), falling back to preset.", bot_key, exc)

    # 2. Fall back to hard-coded preset
    preset = _BOT_PRESETS.get(bot_key, {})
    stub = IBKRMarketDataStub(
        gateway_url=preset.get("gateway_url", "https://localhost:5000"),
        intraday_bar=preset.get("intraday_bar", "5min"),
        swing_bar=preset.get("swing_bar", "30min"),
        intraday_period=preset.get("intraday_period", "1d"),
        swing_period=preset.get("swing_period", "1w"),
        snapshot_fields=preset.get("snapshot_fields", _DEFAULT_SNAPSHOT_FIELDS),
    )
    stub.bot_key = bot_key
    stub.supports = preset.get("supports", ["intraday", "swing"])
    stub.universe = preset.get("universe", [])
    logger.info("for_bot(%s): loaded from built-in preset", bot_key)
    return stub


def universe_snapshot(bot_key: str) -> list[dict[str, Any]]:
    """
    Fetch a market snapshot for every ticker in the bot's universe.

    Returns a list of snapshot dicts (one per ticker).  Tickers that fail
    gracefully return a stub snapshot so the list length is always equal to
    the universe size.

    Parameters
    ----------
    bot_key:
        ``"Rhea_Bot"`` or ``"Triton_Bot"`` (or any key in bots_config.yaml).
    """
    stub = for_bot(bot_key)
    raw_universe = getattr(stub, "_universe", [])
    tickers: list[str] = (
        list(raw_universe)
        if isinstance(raw_universe, (list, tuple))
        else [t.strip() for t in str(raw_universe).split(",") if t.strip()]
    )

    results: list[dict[str, Any]] = []
    for ticker in tickers:
        snap = stub.get_snapshot(ticker)
        results.append(snap.__dict__)
    return results

