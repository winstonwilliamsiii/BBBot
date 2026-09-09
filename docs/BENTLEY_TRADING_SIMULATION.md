# Bentley ML Trading DAG: Simulation Test

The `bentleybot_dag` DAG is simulation-only. It never imports or invokes broker
execution code. It fetches market prices, applies `MeanReversionStrategy`, writes
simulated trade decisions, calculates metrics, and sends the daily report to the
Airflow task log.

## Run locally

Set the following environment variables before triggering the DAG:

```powershell
$env:TRADING_SIMULATION_MODE = "true"
$env:TRADING_TICKERS = "BTC-USD,ETH-USD"
$env:BENTLEY_TRADING_WORK_DIR = "C:\temp\bentley_trading"
airflow dags test bentleybot_dag 2026-09-08
```

The task sequence is:

1. `fetch_market_data`
2. `generate_signals`
3. `execute_trades`
4. `calculate_performance`
5. `send_daily_report`

Successful logs include `SIMULATION MODE`. `execute_trades` creates
`simulated_trades.csv` with `status=simulated` and `execution_mode=SIMULATION MODE`;
it records zero real executions. `calculate_performance` writes
`performance_metrics.json`, while `send_daily_report` sends that report to the
Airflow task log without an external webhook or email call.

## Automated validation

Run the focused test without network or broker access:

```powershell
pytest tests/test_bentleybot_trading_dag.py
```
