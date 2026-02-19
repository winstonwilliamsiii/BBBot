# DCF ANALYSIS FUNDAMENTAL FORECAST
"""
Equity DCF Evaluation Script (Admin Role)
- Pulls historical + current fundamentals from MySQL
- Computes 5–10 year DCF
- Flags equity as Under/Over/Fair valued vs current price
"""

import os
import math
import decimal
import datetime as dt
from typing import List, Dict, Optional

import mysql.connector
import pandas as pd

# ---------- CONFIG ----------

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "admin_user"),
    "password": os.getenv("DB_PASSWORD", "admin_password"),
    "database": os.getenv("DB_NAME", "equity_fundamentals"),
    "port":     int(os.getenv("DB_PORT", "3306")),
}

# DCF assumptions (override per ticker if needed)
DEFAULT_DISCOUNT_RATE = 0.10      # 10%
DEFAULT_TERM_YEARS    = 10        # 5–10 years
DEFAULT_PERP_GROWTH   = 0.02      # 2% terminal growth
DEFAULT_MARGIN_OF_SAFETY = 0.15   # 15% buffer for "undervalued" flag


# ---------- DB LAYER ----------

def get_db_connection():
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn


def fetch_historical_fundamentals(
    ticker: str,
    conn,
    min_years: int = 5
) -> pd.DataFrame:
    """
    Example schema (adjust to your tables):
      table: fundamentals_annual
        - ticker
        - fiscal_year
        - revenue
        - free_cash_flow
        - shares_outstanding
        - net_debt
        - cash
    """
    query = """
        SELECT
            ticker,
            fiscal_year,
            revenue,
            free_cash_flow,
            shares_outstanding,
            net_debt,
            cash
        FROM fundamentals_annual
        WHERE ticker = %s
        ORDER BY fiscal_year DESC
        LIMIT %s
    """
    df = pd.read_sql(query, conn, params=(ticker, min_years))
    if df.empty:
        raise ValueError(f"No fundamentals found for {ticker}")
    return df.sort_values("fiscal_year")  # oldest → newest


def fetch_current_price(ticker: str, conn) -> float:
    """
    Example schema:
      table: prices_latest
        - ticker
        - price
        - as_of_date
    """
    query = """
        SELECT price
        FROM prices_latest
        WHERE ticker = %s
        ORDER BY as_of_date DESC
        LIMIT 1
    """
    cursor = conn.cursor()
    cursor.execute(query, (ticker,))
    row = cursor.fetchone()
    cursor.close()
    if not row:
        raise ValueError(f"No current price found for {ticker}")
    return float(row[0])


# ---------- DCF CORE LOGIC ----------

def estimate_growth_rate_from_history(
    fcf_series: List[float],
    min_floor: float = -0.5,
    max_cap: float = 0.30
) -> float:
    """
    Simple CAGR-based growth estimate from historical FCF.
    Clamp to reasonable bounds.
    """
    if len(fcf_series) < 2:
        return 0.0

    start = fcf_series[0]
    end   = fcf_series[-1]

    if start <= 0 or end <= 0:
        # fallback: flat growth if negative/zero FCF
        return 0.0

    n = len(fcf_series) - 1
    cagr = (end / start) ** (1 / n) - 1
    cagr = max(min(cagr, max_cap), min_floor)
    return cagr


def project_fcf(
    last_fcf: float,
    growth_rate: float,
    years: int
) -> List[float]:
    """
    Project FCF for N years using a constant growth rate.
    """
    projections = []
    fcf = last_fcf
    for _ in range(1, years + 1):
        fcf = fcf * (1 + growth_rate)
        projections.append(fcf)
    return projections


def discount_cash_flows(
    cash_flows: List[float],
    discount_rate: float
) -> List[float]:
    """
    Discount each cash flow back to present value.
    """
    discounted = []
    for t, cf in enumerate(cash_flows, start=1):
        pv = cf / ((1 + discount_rate) ** t)
        discounted.append(pv)
    return discounted


def terminal_value(
    last_fcf: float,
    discount_rate: float,
    perp_growth: float
) -> float:
    """
    Gordon Growth Model for terminal value.
    """
    if discount_rate <= perp_growth:
        # avoid division by zero / nonsense
        perp_growth = discount_rate - 0.01
    tv = last_fcf * (1 + perp_growth) / (discount_rate - perp_growth)
    return tv


def compute_dcf_intrinsic_value(
    ticker: str,
    fundamentals_df: pd.DataFrame,
    discount_rate: float = DEFAULT_DISCOUNT_RATE,
    term_years: int = DEFAULT_TERM_YEARS,
    perp_growth: float = DEFAULT_PERP_GROWTH
) -> Dict[str, float]:
    """
    Returns:
      {
        "equity_value": ...,
        "per_share_value": ...,
        "growth_rate_used": ...,
        "term_years": ...,
      }
    """
    # Use historical FCF to estimate growth
    fcf_hist = fundamentals_df["free_cash_flow"].astype(float).tolist()
    growth_rate = estimate_growth_rate_from_history(fcf_hist)

    last_fcf = fcf_hist[-1]

    # Project FCF for term_years
    projected_fcf = project_fcf(last_fcf, growth_rate, term_years)

    # Discount projected FCF
    discounted_fcf = discount_cash_flows(projected_fcf, discount_rate)

    # Terminal value at end of projection
    tv = terminal_value(projected_fcf[-1], discount_rate, perp_growth)
    tv_pv = tv / ((1 + discount_rate) ** term_years)

    # Enterprise value = sum of discounted FCF + discounted TV
    enterprise_value = sum(discounted_fcf) + tv_pv

    # Use latest row for capital structure
    latest = fundamentals_df.iloc[-1]
    net_debt = float(latest.get("net_debt", 0.0))
    cash    = float(latest.get("cash", 0.0))
    shares  = float(latest.get("shares_outstanding", 1.0))

    # Equity value = EV - net_debt + cash
    equity_value = enterprise_value - net_debt + cash
    per_share_value = equity_value / shares if shares > 0 else float("nan")

    return {
        "equity_value": equity_value,
        "per_share_value": per_share_value,
        "growth_rate_used": growth_rate,
        "term_years": term_years,
    }


def classify_valuation(
    intrinsic_value: float,
    market_price: float,
    margin_of_safety: float = DEFAULT_MARGIN_OF_SAFETY
) -> str:
    """
    Simple classification:
      - "Undervalued" if market_price < intrinsic_value * (1 - margin_of_safety)
      - "Overvalued" if market_price > intrinsic_value * (1 + margin_of_safety)
      - "Fairly Valued" otherwise
    """
    lower_bound = intrinsic_value * (1 - margin_of_safety)
    upper_bound = intrinsic_value * (1 + margin_of_safety)

    if market_price < lower_bound:
        return "Undervalued"
    elif market_price > upper_bound:
        return "Overvalued"
    else:
        return "Fairly Valued"


# ---------- ADMIN-FACING WRAPPER ----------

def run_equity_dcf(
    ticker: str,
    discount_rate: Optional[float] = None,
    term_years: Optional[int] = None,
    perp_growth: Optional[float] = None,
    margin_of_safety: Optional[float] = None,
) -> Dict[str, object]:
    """
    Main admin entrypoint for a single ticker.
    """
    discount_rate   = discount_rate   if discount_rate   is not None else DEFAULT_DISCOUNT_RATE
    term_years      = term_years      if term_years      is not None else DEFAULT_TERM_YEARS
    perp_growth     = perp_growth     if perp_growth     is not None else DEFAULT_PERP_GROWTH
    margin_of_safety = margin_of_safety if margin_of_safety is not None else DEFAULT_MARGIN_OF_SAFETY

    conn = get_db_connection()
    try:
        fundamentals_df = fetch_historical_fundamentals(ticker, conn, min_years=5)
        current_price   = fetch_current_price(ticker, conn)

        dcf_result = compute_dcf_intrinsic_value(
            ticker,
            fundamentals_df,
            discount_rate=discount_rate,
            term_years=term_years,
            perp_growth=perp_growth,
        )

        intrinsic = dcf_result["per_share_value"]
        classification = classify_valuation(
            intrinsic_value=intrinsic,
            market_price=current_price,
            margin_of_safety=margin_of_safety,
        )

        return {
            "ticker": ticker,
            "current_price": current_price,
            "intrinsic_value_per_share": intrinsic,
            "equity_value_total": dcf_result["equity_value"],
            "growth_rate_used": dcf_result["growth_rate_used"],
            "term_years": dcf_result["term_years"],
            "discount_rate": discount_rate,
            "perp_growth": perp_growth,
            "margin_of_safety": margin_of_safety,
            "valuation_label": classification,
        }
    finally:
        conn.close()


# ---------- CLI / TEST HARNESS ----------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Admin DCF valuation for an equity.")
    parser.add_argument("ticker", type=str, help="Ticker symbol (e.g., AAPL)")
    parser.add_argument("--discount", type=float, default=DEFAULT_DISCOUNT_RATE, help="Discount rate (e.g., 0.10)")
    parser.add_argument("--years", type=int, default=DEFAULT_TERM_YEARS, help="Projection horizon in years (5–10)")
    parser.add_argument("--perp_growth", type=float, default=DEFAULT_PERP_GROWTH, help="Perpetual growth rate")
    parser.add_argument("--mos", type=float, default=DEFAULT_MARGIN_OF_SAFETY, help="Margin of safety (e.g., 0.15)")
    args = parser.parse_args()

    result = run_equity_dcf(
        ticker=args.ticker,
        discount_rate=args.discount,
        term_years=args.years,
        perp_growth=args.perp_growth,
        margin_of_safety=args.mos,
    )

    print("=== DCF Valuation ===")
    for k, v in result.items():
        print(f"{k}: {v}")