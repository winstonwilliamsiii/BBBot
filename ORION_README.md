# Orion Bot Guide

## Purpose

Orion is the Mansa_Minerals fund bot. In its current production path, Orion is a
minerals and commodities RSI scanner with YAML-driven runtime settings and an
FFNN model used for monitoring and dashboard refresh.

This guide is intended to be the operator reference for:

- understanding why Orion returns `BUY`, `SELL`, or `HOLD`
- changing Orion parameters safely
- knowing which changes are config-only versus code changes
- extending Orion across broader minerals, gold, and commodity exposures

## Current Live Behavior

Orion currently does these things:

- loads its active settings from [bentley-bot/config/bots/orion.yml](bentley-bot/config/bots/orion.yml)
- scans a configured basket of minerals and commodity proxies each cycle
- uses `GDX` as the default primary and training proxy
- computes RSI from downloaded daily close data
- applies configurable RSI thresholds from YAML
- selects the highest-ranked symbol from the scanned basket
- trains an FFNN model on the configured training symbol for monitoring and
  model refresh
- logs cycle and training runs to MLflow when available
- writes latest status snapshots for dashboard and operations visibility
- sends Discord notifications to Noomo

Important: Orion is now config-driven for symbol selection and RSI thresholds,
but it is still a single selected-signal execution path per cycle rather than a
full multi-order portfolio engine.

## Important Reality Check

There are two Orion definitions in the repo:

- profile/config definition in [bentley-bot/config/bots/orion.yml](bentley-bot/config/bots/orion.yml)
- executable logic in [scripts/orion_bot.py](scripts/orion_bot.py) and [scripts/train_orion_ffnn.py](scripts/train_orion_ffnn.py)

The live Python execution path now reads these Orion YAML fields directly:

- `strategy.primary_symbol`
- `strategy.training_symbol`
- `strategy.scan_symbols`
- `strategy.scan_top_n`
- `risk.rsi_period`
- `risk.rsi_oversold`
- `risk.rsi_overbought`

The live Python execution path now also reads these execution fields:

- `execution.enabled`
- `execution.primary_client`
- `execution.mode`
- `execution.order_type`
- `execution.volume_lots`
- `execution.close_on_reverse`
- `execution.stop_loss_pct`
- `execution.take_profit_pct`
- `execution.symbol_map`

## Main Files

- cycle logic: [scripts/orion_bot.py](scripts/orion_bot.py)
- FFNN trainer: [scripts/train_orion_ffnn.py](scripts/train_orion_ffnn.py)
- orchestration wrapper: [scripts/stars_orchestration.py](scripts/stars_orchestration.py)
- Airflow schedule: [airflow/dags/stars_orchestration_dag.py](airflow/dags/stars_orchestration_dag.py)
- bot profile: [bentley-bot/config/bots/orion.yml](bentley-bot/config/bots/orion.yml)
- screener file: [bentley-bot/config/orion_minerals_fundamentals.csv](bentley-bot/config/orion_minerals_fundamentals.csv)
- latest training snapshot: [airflow/config/logs/orion_training_latest.json](airflow/config/logs/orion_training_latest.json)
- latest cycle snapshot: [airflow/config/logs/orion_cycle_latest.json](airflow/config/logs/orion_cycle_latest.json)

## Signal Logic

The live cycle logic in [scripts/orion_bot.py](scripts/orion_bot.py) is now:

1. Load Orion settings from YAML.
2. Scan the configured symbols from `scan_symbols`.
3. Download recent daily data for each symbol with `yfinance`.
4. Fall back to deterministic synthetic data if market data is unavailable.
5. Compute RSI using the configured `rsi_period`.
6. Apply the configured `rsi_oversold` and `rsi_overbought` thresholds.
7. Rank the basket and select the strongest symbol for the cycle result.

This means a `HOLD` signal is not a malfunction. It simply means the current RSI
is in the neutral band.

## Why Orion Often Shows HOLD

If you still see `HOLD`, it now means none of the scanned symbols produced a
strong enough overbought or oversold signal under the configured thresholds.

## Parameters You Can Change Today

These changes work immediately because the current Python scripts already use
them.

### 1. Cycle lookback window

Command:

```powershell
python scripts/orion_bot.py --days 180
```

Effect:

- changes how much price history Orion pulls before calculating RSI
- does not change the YAML-configured RSI period itself

When to change it:

- increase if you want more historical context for diagnostics
- decrease if you want faster checks with less history

### 2. FFNN training lookback window

Command:

```powershell
python scripts/train_orion_ffnn.py --days 365 --max-iter 250 --hidden-layer-sizes 32 16
```

Effect:

- changes how much history is used for the configured training symbol
- longer windows generally provide more samples but may blend multiple market
  regimes

### 3. FFNN model complexity

Command:

```powershell
python scripts/train_orion_ffnn.py --days 365 --max-iter 400 --hidden-layer-sizes 64 32
```

Effect:

- changes hidden layer widths and training iterations
- larger models may fit more pattern detail but can also overfit noisy data

### 4. YAML strategy and risk settings

Live control surface in [bentley-bot/config/bots/orion.yml](bentley-bot/config/bots/orion.yml):

- `strategy.primary_symbol`
- `strategy.training_symbol`
- `strategy.scan_symbols`
- `strategy.scan_top_n`
- `risk.rsi_period`
- `risk.rsi_oversold`
- `risk.rsi_overbought`

### 5. Discord and MLflow behavior

Environment variables used by Orion:

- `DISCORD_WEBHOOK_NOOMO`
- `MLFLOW_TRACKING_URI`
- `BENTLEY_REPO_ROOT`

## Parameters That Require Code Changes

These are the changes that still require code work beyond the new YAML-driven
runtime controls.

### 1. Change the tracked asset

Current default primary asset: `GDX`

Code locations:

- [scripts/orion_bot.py](scripts/orion_bot.py)
- [scripts/train_orion_ffnn.py](scripts/train_orion_ffnn.py)

You can now change the configured basket in YAML, but code work is still needed
if you want different ranking logic, different feature engineering, or actual
multi-order execution.

Relevant symbols for Orion include:

- `GDX` for gold miners ETF
- `GDXJ` for junior gold miners ETF
- `SLV` for silver exposure
- `COPX` for copper miners
- `PICK` for mining equities basket
- a basket of symbols if you want Orion to scan multiple commodity-related names

### 2. Change ranking logic

The thresholds are now config-driven, but the basket ranking heuristic is still
implemented in [scripts/orion_bot.py](scripts/orion_bot.py).

If you want more signal frequency, common threshold experiments are:

- `35 / 65` for more trades
- `40 / 60` for much more sensitivity

Tradeoff:

- more frequent signals usually means more noise and more false positives

### 3. Change the RSI period

Current default live period: `14`

Shorter period examples:

- `7` gives faster, noisier reactions
- `9` is a moderate increase in sensitivity

Longer period examples:

- `21` gives slower, more stable signals

### 4. Add real execution

Scanning and selecting a symbol is now implemented, and Orion can place broker
orders through MT5 when:

- execution is enabled in YAML
- the selected scan symbol has an executable broker mapping
- MT5 credentials and REST bridge are available

## Recommended Tuning Path

If the goal is to keep the current Orion structure but make it more actionable,
use this order of operations:

1. Keep `GDX` as the default primary symbol for now.
2. Use the basket scan to compare how often `GDX`, `GDXJ`, `GLD`, and miners
  generate actionable RSI extremes.
3. Adjust thresholds only after observing scan behavior across several mornings.
4. Add broker execution only after the selection logic is stable.

## What the YAML Profile Means Today

The Orion profile at [bentley-bot/config/bots/orion.yml](bentley-bot/config/bots/orion.yml)
is now part of the live runtime control surface.

Notable values there:

- fund: `Mansa Minerals`
- execution venue: `ftmo`
- execution mode: `paper`
- execution enabled: `false`
- strategy label: `Orion_Minerals_RSI_Scanner`
- universe: `Minerals_Commodities`
- timeframe: `H1`
- position size: `2200`
- primary symbol: `GDX`
- training symbol: `GDX`
- scan basket includes `GDX`, `GDXJ`, `GLD`, `NEM`, `FCX`, `SCCO`, `TECK`, `AA`, `RIO`
- risk thresholds: `rsi_period: 14`, `rsi_oversold: 35`, `rsi_overbought: 65`

Important: not every scanned equity or ETF is directly tradable on MT5/FTMO, so
Orion uses `execution.symbol_map` to translate scan symbols into executable venue
symbols such as `XAUUSD` or `COPPER`.

## Schedule and Orchestration

Orion is wired into `stars_orchestration` and scheduled for:

- 7:00 AM Monday through Friday
- timezone: `America/New_York`

Within orchestration:

- Orion training runs every scheduled cycle
- Orion cycle evaluation also runs in the orchestration path
- Discord notifications are sent to Noomo
- latest results are persisted to JSON snapshots for dashboard visibility

## Runtime Outputs

Training output snapshot:

- [airflow/config/logs/orion_training_latest.json](airflow/config/logs/orion_training_latest.json)

Typical fields:

- `status`
- `mlflow_logged`
- `run_id`
- `accuracy`
- `precision`
- `recall`
- `model_path`
- `scaler_path`
- `discord`

Cycle output snapshot:

- [airflow/config/logs/orion_cycle_latest.json](airflow/config/logs/orion_cycle_latest.json)

Typical fields:

- `selected_symbol`
- `execution`
- `symbols_scanned`
- `scan_results`
- `latest_price`
- `rsi_value`
- `mlflow_logged`
- `discord`

## Manual Commands

Run one Orion cycle:

```powershell
python scripts/orion_bot.py --days 180
```

Run one FFNN training pass:

```powershell
python scripts/train_orion_ffnn.py --days 365 --max-iter 250 --hidden-layer-sizes 32 16
```

Trigger the orchestration DAG:

```powershell
docker compose -f docker/docker-compose-airflow.yml exec airflow-webserver airflow dags trigger stars_orchestration
```

## Practical Change Guide

If you want Orion to remain conservative:

- keep `GDX` as primary symbol
- keep `RSI(14)`
- keep `35 / 65`

If you want Orion to trade more often without redesigning the bot:

- keep the current basket
- test `RSI(14)` with `40 / 60`

If you want Orion to better represent mining and commodity opportunity:

- adjust `strategy.scan_symbols` and `strategy.primary_symbol`
- then evaluate whether the current FFNN features still make sense

If you want Orion to become a true multi-asset minerals strategy:

- keep the new basket scanner
- execution now places MT5 orders for mapped symbols
- next expand symbol mappings and broker-specific position sizing rules

## Current Status

Verified currently:

- Orion weekday schedule is active
- Orion training works in Airflow
- Orion cycle logging works in Airflow
- MLflow logging is working again for the validated path
- Noomo Discord notifications are working

## Known Limitations

- Orion still returns a single selected symbol per cycle, not a portfolio of trades
- execution currently depends on explicit `execution.symbol_map` mappings for
  MT5-compatible symbols
- synthetic fallback data can preserve system continuity, but it should not be
  mistaken for real market confirmation

## Suggested Next Upgrade

The cleanest next enhancement for Orion would be:

1. expand Orion broker mappings beyond gold and copper proxies
2. make FFNN feature engineering configurable by symbol universe
3. decide whether Orion should place one best trade or manage a small basket
