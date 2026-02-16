"""
Equity DCF (Discounted Cash Flow) Analysis Component
====================================================
Admin-level fundamental analysis tool for equity valuation.

Features:
- Pulls historical fundamentals from MySQL database
- Computes 5-10 year DCF projections
- Classifies equities as Undervalued/Overvalued/Fair valued
- Integrates with Bentley Budget Bot dashboard

Dependencies:
- MySQL database with fundamentals_annual and prices_latest tables
- mysql-connector-python
- pandas

Environment Variables:
- DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
"""

import os
import math
import datetime as dt
from typing import List, Dict, Optional, Tuple
import logging

try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- CONFIG ----------

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "Bentley_Budget"),
    "port": int(os.getenv("DB_PORT", "3306")),
}

# DCF assumptions (override per ticker if needed)
DEFAULT_DISCOUNT_RATE = 0.10  # 10%
DEFAULT_TERM_YEARS = 10  # 5-10 years
DEFAULT_PERP_GROWTH = 0.02  # 2% terminal growth
DEFAULT_MARGIN_OF_SAFETY = 0.15  # 15% buffer for "undervalued" flag


# ---------- DB LAYER ----------

def get_db_connection():
    """Create and return a MySQL database connection."""
    if not MYSQL_AVAILABLE:
        raise ImportError("mysql-connector-python is required for DCF analysis")
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise


def fetch_historical_fundamentals(
    ticker: str,
    conn,
    min_years: int = 5
) -> pd.DataFrame:
    """
    Fetch historical fundamental data for a ticker.
    
    Expected schema:
      table: fundamentals_annual
        - ticker (VARCHAR)
        - fiscal_year (INT)
        - revenue (DECIMAL)
        - free_cash_flow (DECIMAL)
        - shares_outstanding (DECIMAL)
        - net_debt (DECIMAL)
        - cash (DECIMAL)
    
    Args:
        ticker: Stock ticker symbol
        conn: MySQL connection object
        min_years: Minimum years of historical data to fetch
    
    Returns:
        DataFrame with historical fundamentals sorted by fiscal_year
    
    Raises:
        ValueError: If no data found for ticker
    """
    if not PANDAS_AVAILABLE:
        raise ImportError("pandas is required for DCF analysis")
    
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
    
    try:
        df = pd.read_sql(query, conn, params=(ticker, min_years))
        if df.empty:
            raise ValueError(f"No fundamentals found for {ticker}")
        
        # Sort oldest to newest for analysis
        return df.sort_values("fiscal_year")
    except Exception as e:
        logger.error(f"Error fetching fundamentals for {ticker}: {e}")
        raise


def fetch_current_price(ticker: str, conn) -> float:
    """
    Fetch the most recent market price for a ticker.
    
    Expected schema:
      table: prices_latest
        - ticker (VARCHAR)
        - price (DECIMAL)
        - as_of_date (DATE)
    
    Args:
        ticker: Stock ticker symbol
        conn: MySQL connection object
    
    Returns:
        Current market price as float
    
    Raises:
        ValueError: If no price found for ticker
    """
    query = """
        SELECT price
        FROM prices_latest
        WHERE ticker = %s
        ORDER BY as_of_date DESC
        LIMIT 1
    """
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, (ticker,))
        row = cursor.fetchone()
        cursor.close()
        
        if not row:
            raise ValueError(f"No current price found for {ticker}")
        
        return float(row[0])
    except Exception as e:
        logger.error(f"Error fetching price for {ticker}: {e}")
        raise


# ---------- DCF CORE LOGIC ----------

def estimate_growth_rate_from_history(
    fcf_series: List[float],
    min_floor: float = -0.5,
    max_cap: float = 0.30
) -> float:
    """
    Estimate growth rate from historical FCF using CAGR.
    
    Args:
        fcf_series: List of historical free cash flows
        min_floor: Minimum allowed growth rate (default -50%)
        max_cap: Maximum allowed growth rate (default 30%)
    
    Returns:
        Estimated growth rate (clamped to reasonable bounds)
    """
    if len(fcf_series) < 2:
        logger.warning("Insufficient FCF history for growth estimation")
        return 0.0

    start = fcf_series[0]
    end = fcf_series[-1]

    # Handle negative or zero FCF
    if start <= 0 or end <= 0:
        logger.warning("Negative or zero FCF detected, using flat growth")
        return 0.0

    # Calculate CAGR
    n = len(fcf_series) - 1
    try:
        cagr = (end / start) ** (1 / n) - 1
        # Clamp to reasonable bounds
        cagr = max(min(cagr, max_cap), min_floor)
        logger.info(f"Estimated growth rate: {cagr:.2%}")
        return cagr
    except (ValueError, ZeroDivisionError) as e:
        logger.error(f"Error calculating CAGR: {e}")
        return 0.0


def project_fcf(
    last_fcf: float,
    growth_rate: float,
    years: int
) -> List[float]:
    """
    Project future FCF using constant growth rate.
    
    Args:
        last_fcf: Most recent free cash flow
        growth_rate: Annual growth rate
        years: Number of years to project
    
    Returns:
        List of projected FCF values
    """
    projections = []
    fcf = last_fcf
    
    for year in range(1, years + 1):
        fcf = fcf * (1 + growth_rate)
        projections.append(fcf)
        logger.debug(f"Year {year} projected FCF: ${fcf:,.0f}")
    
    return projections


def discount_cash_flows(
    cash_flows: List[float],
    discount_rate: float
) -> List[float]:
    """
    Discount future cash flows to present value.
    
    Args:
        cash_flows: List of future cash flows
        discount_rate: Discount rate (WACC)
    
    Returns:
        List of discounted present values
    """
    discounted = []
    
    for t, cf in enumerate(cash_flows, start=1):
        pv = cf / ((1 + discount_rate) ** t)
        discounted.append(pv)
        logger.debug(f"Year {t} PV: ${pv:,.0f}")
    
    return discounted


def terminal_value(
    last_fcf: float,
    discount_rate: float,
    perp_growth: float
) -> float:
    """
    Calculate terminal value using Gordon Growth Model.
    
    Args:
        last_fcf: Last projected free cash flow
        discount_rate: Discount rate (WACC)
        perp_growth: Perpetual growth rate
    
    Returns:
        Terminal value
    
    Raises:
        ValueError: If discount_rate <= perp_growth
    """
    if discount_rate <= perp_growth:
        # Prevent division by zero or negative denominator
        perp_growth = discount_rate - 0.01
        logger.warning(f"Adjusted perpetual growth to {perp_growth:.2%}")
    
    try:
        tv = last_fcf * (1 + perp_growth) / (discount_rate - perp_growth)
        logger.info(f"Terminal value: ${tv:,.0f}")
        return tv
    except ZeroDivisionError:
        logger.error("Terminal value calculation failed")
        return 0.0


def compute_dcf_intrinsic_value(
    ticker: str,
    fundamentals_df: pd.DataFrame,
    discount_rate: float = DEFAULT_DISCOUNT_RATE,
    term_years: int = DEFAULT_TERM_YEARS,
    perp_growth: float = DEFAULT_PERP_GROWTH
) -> Dict[str, float]:
    """
    Compute DCF-based intrinsic equity value.
    
    Args:
        ticker: Stock ticker symbol
        fundamentals_df: DataFrame with historical fundamentals
        discount_rate: Discount rate (WACC)
        term_years: Projection horizon (years)
        perp_growth: Perpetual growth rate
    
    Returns:
        Dictionary with:
            - equity_value: Total equity value
            - per_share_value: Intrinsic value per share
            - growth_rate_used: Estimated growth rate
            - term_years: Projection period
    """
    logger.info(f"Computing DCF for {ticker}")
    
    # Estimate growth from historical FCF
    fcf_hist = fundamentals_df["free_cash_flow"].astype(float).tolist()
    growth_rate = estimate_growth_rate_from_history(fcf_hist)

    last_fcf = fcf_hist[-1]
    logger.info(f"Last FCF: ${last_fcf:,.0f}, Growth rate: {growth_rate:.2%}")

    # Project FCF
    projected_fcf = project_fcf(last_fcf, growth_rate, term_years)

    # Discount projected FCF
    discounted_fcf = discount_cash_flows(projected_fcf, discount_rate)

    # Calculate terminal value
    tv = terminal_value(projected_fcf[-1], discount_rate, perp_growth)
    tv_pv = tv / ((1 + discount_rate) ** term_years)

    # Enterprise value = PV of FCF + PV of terminal value
    enterprise_value = sum(discounted_fcf) + tv_pv
    logger.info(f"Enterprise value: ${enterprise_value:,.0f}")

    # Extract capital structure from latest data
    latest = fundamentals_df.iloc[-1]
    net_debt = float(latest.get("net_debt", 0.0))
    cash = float(latest.get("cash", 0.0))
    shares = float(latest.get("shares_outstanding", 1.0))

    # Equity value = EV - net_debt + cash
    equity_value = enterprise_value - net_debt + cash
    per_share_value = equity_value / shares if shares > 0 else float("nan")
    
    logger.info(f"Equity value: ${equity_value:,.0f}, Per share: ${per_share_value:.2f}")

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
) -> Tuple[str, float]:
    """
    Classify stock valuation relative to market price.
    
    Args:
        intrinsic_value: DCF intrinsic value per share
        market_price: Current market price
        margin_of_safety: Buffer percentage for classification
    
    Returns:
        Tuple of (classification, upside_percentage)
        - Classification: "Undervalued", "Overvalued", or "Fairly Valued"
        - Upside: Percentage difference (positive = undervalued)
    """
    lower_bound = intrinsic_value * (1 - margin_of_safety)
    upper_bound = intrinsic_value * (1 + margin_of_safety)
    
    upside = ((intrinsic_value - market_price) / market_price) * 100

    if market_price < lower_bound:
        classification = "Undervalued"
    elif market_price > upper_bound:
        classification = "Overvalued"
    else:
        classification = "Fairly Valued"
    
    logger.info(f"Classification: {classification}, Upside: {upside:.1f}%")
    return classification, upside


# ---------- ADMIN-FACING WRAPPER ----------

def run_equity_dcf(
    ticker: str,
    discount_rate: Optional[float] = None,
    term_years: Optional[int] = None,
    perp_growth: Optional[float] = None,
    margin_of_safety: Optional[float] = None,
) -> Dict[str, object]:
    """
    Main entry point for DCF analysis of a single ticker.
    
    Args:
        ticker: Stock ticker symbol
        discount_rate: Custom discount rate (uses default if None)
        term_years: Custom projection period (uses default if None)
        perp_growth: Custom perpetual growth rate (uses default if None)
        margin_of_safety: Custom margin of safety (uses default if None)
    
    Returns:
        Dictionary with complete DCF analysis results
    
    Raises:
        ImportError: If required packages not available
        ValueError: If no data found for ticker
        Exception: For database or calculation errors
    """
    # Use defaults if not specified
    discount_rate = discount_rate if discount_rate is not None else DEFAULT_DISCOUNT_RATE
    term_years = term_years if term_years is not None else DEFAULT_TERM_YEARS
    perp_growth = perp_growth if perp_growth is not None else DEFAULT_PERP_GROWTH
    margin_of_safety = margin_of_safety if margin_of_safety is not None else DEFAULT_MARGIN_OF_SAFETY

    logger.info(f"Starting DCF analysis for {ticker}")
    
    conn = get_db_connection()
    try:
        # Fetch data
        fundamentals_df = fetch_historical_fundamentals(ticker, conn, min_years=5)
        current_price = fetch_current_price(ticker, conn)

        # Compute DCF
        dcf_result = compute_dcf_intrinsic_value(
            ticker,
            fundamentals_df,
            discount_rate=discount_rate,
            term_years=term_years,
            perp_growth=perp_growth,
        )

        # Classify valuation
        intrinsic = dcf_result["per_share_value"]
        classification, upside = classify_valuation(
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
            "upside_percent": upside,
            "timestamp": dt.datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"DCF analysis failed for {ticker}: {e}")
        raise
    finally:
        conn.close()


# ---------- CLI / TEST HARNESS ----------

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Admin DCF valuation for an equity.")
    parser.add_argument("ticker", type=str, help="Ticker symbol (e.g., AAPL)")
    parser.add_argument("--discount", type=float, default=DEFAULT_DISCOUNT_RATE, help="Discount rate (e.g., 0.10)")
    parser.add_argument("--years", type=int, default=DEFAULT_TERM_YEARS, help="Projection horizon in years (5-10)")
    parser.add_argument("--perp_growth", type=float, default=DEFAULT_PERP_GROWTH, help="Perpetual growth rate")
    parser.add_argument("--mos", type=float, default=DEFAULT_MARGIN_OF_SAFETY, help="Margin of safety (e.g., 0.15)")
    
    args = parser.parse_args()

    try:
        result = run_equity_dcf(
            ticker=args.ticker,
            discount_rate=args.discount,
            term_years=args.years,
            perp_growth=args.perp_growth,
            margin_of_safety=args.mos,
        )

        print("\n" + "=" * 50)
        print(f"DCF VALUATION ANALYSIS: {result['ticker']}")
        print("=" * 50)
        print(f"Current Price:        ${result['current_price']:.2f}")
        print(f"Intrinsic Value:      ${result['intrinsic_value_per_share']:.2f}")
        print(f"Valuation:            {result['valuation_label']}")
        print(f"Upside/Downside:      {result['upside_percent']:.1f}%")
        print(f"\nGrowth Rate Used:     {result['growth_rate_used']:.2%}")
        print(f"Discount Rate:        {result['discount_rate']:.2%}")
        print(f"Projection Period:    {result['term_years']} years")
        print(f"Terminal Growth:      {result['perp_growth']:.2%}")
        print(f"Margin of Safety:     {result['margin_of_safety']:.2%}")
        print(f"Total Equity Value:   ${result['equity_value_total']:,.0f}")
        print("=" * 50 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        exit(1)
