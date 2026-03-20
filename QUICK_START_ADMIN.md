# Quick Start - Jupicita Strategy Scope

**Updated:** March 18, 2026  
**Status:** Active direction

## Change Summary

The previous Admin Control Center / Bot Manager page has been removed from the Streamlit app.

Current focus for Jupicita is:

- Alpha generation via price forecasting
- Portfolio optimization
- Simulated rebalancing guidance
- Execution-aware deployment

## Default Strategy Label

Jupicita strategy is set as a proposed default and can be overridden once the exact production label is finalized.

## Immediate Priorities

1. Forecasting layer

- Define feature set, horizon, and retraining cadence.
- Produce confidence-aware return forecasts for tradable universe candidates.

1. Optimization layer

- Translate forecasts into constrained portfolio weights.
- Include liquidity, turnover, and exposure constraints.

1. Simulated rebalancing layer

- Run paper rebalances on schedule and event triggers.
- Track slippage assumptions, drift, and cost-aware outcomes.

1. Execution-aware deployment

- Attach order sizing and venue/broker execution constraints.
- Gate live execution using health checks and risk controls.

## Run the Main App

```powershell
cd C:\Users\winst\BentleyBudgetBot
streamlit run streamlit_app.py
```

## Notes

- This file is intentionally retained as a transition pointer from earlier admin-oriented docs.
- If needed, it can be renamed in a follow-up cleanup once links are updated.
