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

import requests

try:
    # Keep DB resolution consistent with the rest of the frontend stack.
    from frontend.utils.secrets_helper import get_mysql_config
    MYSQL_CONFIG_HELPER_AVAILABLE = True
except ImportError:
    MYSQL_CONFIG_HELPER_AVAILABLE = False

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

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- CONFIG ----------

def _build_db_config() -> Dict[str, object]:
    """
    Build MySQL connection config with a consistent precedence strategy.

    Priority:
    1) Explicit process env vars (MYSQL_* / DB_*)
    2) Shared frontend helper (`get_mysql_config`) fallback
    3) Local defaults
    """
    env_host = os.getenv("MYSQL_HOST") or os.getenv("DB_HOST")
    env_port = os.getenv("MYSQL_PORT") or os.getenv("DB_PORT")
    env_user = os.getenv("MYSQL_USER") or os.getenv("DB_USER")
    env_password = os.getenv("MYSQL_PASSWORD") or os.getenv("DB_PASSWORD")
    env_database = os.getenv("MYSQL_DATABASE") or os.getenv("DB_NAME")

    # Prefer explicit env vars when present (typical local dev flow).
    if any([env_host, env_port, env_user, env_password, env_database]):
        return {
            "host": env_host or "127.0.0.1",
            "user": env_user or "root",
            "password": env_password or "",
            "database": env_database or "mansa_bot",
            "port": int(env_port or "3306"),
        }

    requested_db = "mansa_bot"
    if MYSQL_CONFIG_HELPER_AVAILABLE:
        try:
            return get_mysql_config(database=requested_db)
        except Exception as e:
            logger.warning(f"Falling back to local default DB config: {e}")

    return {
        "host": "127.0.0.1",
        "user": "root",
        "password": "",
        "database": requested_db,
        "port": 3306,
    }

# DCF assumptions (override per ticker if needed)
DEFAULT_DISCOUNT_RATE = 0.10  # 10%
DEFAULT_TERM_YEARS = 10  # 5-10 years
DEFAULT_PERP_GROWTH = 0.02  # 2% terminal growth
DEFAULT_MARGIN_OF_SAFETY = 0.15  # 15% buffer for "undervalued" flag

DCF_REQUIRED_TABLES = ("fundamentals_annual", "prices_latest")


# ---------- DB LAYER ----------

def get_db_connection():
    """Create and return a MySQL database connection."""
    if not MYSQL_AVAILABLE:
        raise ImportError(
            "mysql-connector-python is required for DCF analysis"
        )

    db_config = _build_db_config()

    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as e:
        # Common local-dev mismatch: Docker MySQL is exposed on 3307.
        if (
            getattr(e, "errno", None) == 1049
            and db_config.get("port") == 3306
            and str(db_config.get("host")) in ("127.0.0.1", "localhost")
        ):
            alt_config = dict(db_config)
            alt_config["port"] = 3307
            logger.warning(
                "Primary MySQL connection failed with unknown database on port 3306. "
                "Retrying DCF connection on port 3307..."
            )
            try:
                return mysql.connector.connect(**alt_config)
            except mysql.connector.Error:
                # Fall through to DB bootstrap attempt on original config.
                pass

        if getattr(e, "errno", None) == 1049:
            database = str(db_config.get("database") or "").strip()
            if not database:
                logger.error(f"Database connection failed: {e}")
                raise

            # Create the requested schema if it does not exist, then reconnect.
            bootstrap_config = dict(db_config)
            bootstrap_config.pop("database", None)
            try:
                bootstrap_conn = mysql.connector.connect(**bootstrap_config)
                bootstrap_cursor = bootstrap_conn.cursor()
                bootstrap_cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{database}`"
                )
                bootstrap_conn.commit()
                bootstrap_cursor.close()
                bootstrap_conn.close()
                logger.info(
                    f"Created missing MySQL database '{database}' "
                    "for DCF analysis"
                )
                return mysql.connector.connect(**db_config)
            except mysql.connector.Error as bootstrap_error:
                logger.error(f"Database bootstrap failed: {bootstrap_error}")
                raise

        logger.error(f"Database connection failed: {e}")
        raise


def _table_exists(conn, table_name: str, database: Optional[str] = None) -> bool:
    """Check whether a table exists in a given schema."""
    try:
        cursor = conn.cursor()
        if database:
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
                LIMIT 1
                """,
                (database, table_name),
            )
        else:
            cursor.execute(
                """
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = DATABASE() AND table_name = %s
                LIMIT 1
                """,
                (table_name,),
            )
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists
    except Exception:
        return False


def _switch_database(conn, database: str) -> None:
    """Switch the active schema on an open connection."""
    cursor = conn.cursor()
    cursor.execute(f"USE `{database}`")
    cursor.close()


def _create_dcf_tables_if_missing(conn) -> None:
    """Create DCF tables in the current schema if they do not exist."""
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS fundamentals_annual (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            ticker VARCHAR(10) NOT NULL,
            fiscal_year INT NOT NULL,
            revenue DECIMAL(20,2) DEFAULT NULL,
            free_cash_flow DECIMAL(20,2) DEFAULT NULL,
            shares_outstanding DECIMAL(20,2) DEFAULT NULL,
            net_debt DECIMAL(20,2) DEFAULT 0,
            cash DECIMAL(20,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_ticker_year (ticker, fiscal_year),
            INDEX idx_ticker (ticker),
            INDEX idx_fiscal_year (fiscal_year)
        ) ENGINE=InnoDB
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS prices_latest (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            ticker VARCHAR(10) NOT NULL,
            price DECIMAL(12,4) NOT NULL,
            as_of_date DATE NOT NULL,
            volume BIGINT DEFAULT NULL,
            market_cap DECIMAL(20,2) DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_ticker_date (ticker, as_of_date),
            INDEX idx_ticker (ticker),
            INDEX idx_as_of_date (as_of_date)
        ) ENGINE=InnoDB
        """
    )
    conn.commit()
    cursor.close()


def ensure_dcf_schema(conn) -> str:
    """
    Ensure DCF tables are available on the current connection.

    Strategy:
    1) Use current schema if both tables exist.
    2) Try known alternate schemas and switch if both tables exist there.
    3) Create missing DCF tables in current schema to prevent SQL 1146 failures.
    """
    current_db = (getattr(conn, "database", None) or "").strip()
    if not current_db:
        cursor = conn.cursor()
        cursor.execute("SELECT DATABASE()")
        row = cursor.fetchone()
        cursor.close()
        current_db = str(row[0]) if row and row[0] else ""

    if current_db and all(_table_exists(conn, t, current_db) for t in DCF_REQUIRED_TABLES):
        return current_db

    candidate_dbs = []
    for db_name in (
        current_db,
        os.getenv("MYSQL_DATABASE"),
        os.getenv("DB_NAME"),
        "mansa_bot",
        "Bentley_Budget",
        "bentley_budget",
    ):
        db_name = (db_name or "").strip()
        if db_name and db_name not in candidate_dbs:
            candidate_dbs.append(db_name)

    for db_name in candidate_dbs:
        if db_name == current_db:
            continue
        if all(_table_exists(conn, t, db_name) for t in DCF_REQUIRED_TABLES):
            _switch_database(conn, db_name)
            logger.warning(
                "DCF tables not found in '%s'; switched DCF queries to '%s'",
                current_db or "(unknown)",
                db_name,
            )
            return db_name

    # Last resort: create tables in the active schema so DCF query path remains stable.
    _create_dcf_tables_if_missing(conn)
    logger.warning(
        "DCF tables were missing in '%s' and were auto-created. "
        "Populate fundamentals_annual/prices_latest (or run scripts/setup_dcf_db.py) "
        "for full analysis results.",
        current_db or "current database",
    )
    return current_db or ""


def _safe_float(value, default: float = 0.0) -> float:
    """Safely cast numeric-like API values to float."""
    if value is None:
        return default
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned in ("", "None", "null", "-"):
            return default
        value = cleaned.replace(",", "")
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _fetch_alpha_vantage_fundamentals(ticker: str, min_years: int) -> List[Dict[str, float]]:
    """Fetch annual fundamentals from Alpha Vantage endpoints."""
    api_key = (os.getenv("ALPHA_VANTAGE_API_KEY") or "").strip()
    if not api_key:
        return []

    base_url = "https://www.alphavantage.co/query"

    def _av_call(function_name: str) -> Dict[str, object]:
        resp = requests.get(
            base_url,
            params={"function": function_name, "symbol": ticker, "apikey": api_key},
            timeout=20,
        )
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, dict) and ("Note" in payload or "Error Message" in payload):
            return {}
        return payload if isinstance(payload, dict) else {}

    overview = _av_call("OVERVIEW")
    cash_flow = _av_call("CASH_FLOW")
    income = _av_call("INCOME_STATEMENT")
    balance = _av_call("BALANCE_SHEET")

    cf_reports = {str(r.get("fiscalDateEnding", ""))[:4]: r for r in cash_flow.get("annualReports", [])}
    inc_reports = {str(r.get("fiscalDateEnding", ""))[:4]: r for r in income.get("annualReports", [])}
    bal_reports = {str(r.get("fiscalDateEnding", ""))[:4]: r for r in balance.get("annualReports", [])}

    candidate_years = sorted(
        [y for y in set(cf_reports.keys()) | set(inc_reports.keys()) | set(bal_reports.keys()) if y.isdigit()],
        reverse=True,
    )

    shares_outstanding = _safe_float(overview.get("SharesOutstanding"), 1.0)
    results: List[Dict[str, float]] = []

    for year_str in candidate_years:
        cf = cf_reports.get(year_str, {})
        inc = inc_reports.get(year_str, {})
        bal = bal_reports.get(year_str, {})

        op_cf = _safe_float(cf.get("operatingCashflow"), 0.0)
        capex = _safe_float(cf.get("capitalExpenditures"), 0.0)
        fcf = _safe_float(cf.get("freeCashFlow"), op_cf + capex)

        if fcf == 0.0:
            continue

        cash_value = _safe_float(
            bal.get("cashAndCashEquivalentsAtCarryingValue"),
            _safe_float(bal.get("cashAndShortTermInvestments"), 0.0),
        )
        total_debt = _safe_float(
            bal.get("totalDebt"),
            _safe_float(bal.get("shortLongTermDebtTotal"), 0.0),
        )

        results.append(
            {
                "fiscal_year": int(year_str),
                "revenue": _safe_float(inc.get("totalRevenue"), 0.0),
                "free_cash_flow": fcf,
                "shares_outstanding": shares_outstanding,
                "net_debt": total_debt - cash_value,
                "cash": cash_value,
            }
        )
        if len(results) >= max(min_years, 5):
            break

    return results


def _get_yf_row(frame, labels: List[str]):
    """Return first matching row from a yfinance statement DataFrame."""
    if frame is None or getattr(frame, "empty", True):
        return None
    index_map = {str(i).lower(): i for i in frame.index}
    for label in labels:
        matched = index_map.get(label.lower())
        if matched is not None:
            return frame.loc[matched]
    return None


def _fetch_yfinance_fundamentals(ticker: str, min_years: int) -> List[Dict[str, float]]:
    """Fetch annual fundamentals from yfinance financial statements."""
    if not YFINANCE_AVAILABLE:
        return []

    try:
        tk = yf.Ticker(ticker)
        cashflow = tk.cashflow
        income = tk.financials
        balance = tk.balance_sheet

        shares = _safe_float((tk.info or {}).get("sharesOutstanding"), 1.0)

        fcf_row = _get_yf_row(cashflow, ["Free Cash Flow"])
        opcf_row = _get_yf_row(cashflow, ["Operating Cash Flow", "Total Cash From Operating Activities"])
        capex_row = _get_yf_row(cashflow, ["Capital Expenditure", "Capital Expenditures"])
        rev_row = _get_yf_row(income, ["Total Revenue"])
        debt_row = _get_yf_row(balance, ["Total Debt", "Long Term Debt"])
        cash_row = _get_yf_row(balance, ["Cash And Cash Equivalents", "Cash", "Cash Cash Equivalents And Short Term Investments"])

        columns = []
        for frame in (cashflow, income, balance):
            if frame is not None and not frame.empty:
                columns.extend(list(frame.columns))

        years = sorted({int(c.year) for c in columns if hasattr(c, "year")}, reverse=True)

        rows: List[Dict[str, float]] = []
        for year in years:
            year_col = None
            for c in columns:
                if hasattr(c, "year") and int(c.year) == year:
                    year_col = c
                    break
            if year_col is None:
                continue

            fcf_val = 0.0
            if fcf_row is not None:
                fcf_val = _safe_float(fcf_row.get(year_col), 0.0)
            if fcf_val == 0.0:
                fcf_val = _safe_float(opcf_row.get(year_col), 0.0) + _safe_float(capex_row.get(year_col), 0.0)
            if fcf_val == 0.0:
                continue

            cash_val = _safe_float(cash_row.get(year_col), 0.0)
            debt_val = _safe_float(debt_row.get(year_col), 0.0)
            rows.append(
                {
                    "fiscal_year": int(year),
                    "revenue": _safe_float(rev_row.get(year_col), 0.0),
                    "free_cash_flow": fcf_val,
                    "shares_outstanding": shares,
                    "net_debt": debt_val - cash_val,
                    "cash": cash_val,
                }
            )
            if len(rows) >= max(min_years, 5):
                break

        return rows
    except Exception as e:
        logger.warning("yfinance fundamentals fetch failed for %s: %s", ticker, e)
        return []


def _upsert_fundamentals(conn, ticker: str, rows: List[Dict[str, float]]) -> int:
    """Persist fetched annual fundamentals to MySQL for DCF reuse."""
    if not rows:
        return 0

    cursor = conn.cursor()
    upsert_sql = """
        INSERT INTO fundamentals_annual (
            ticker, fiscal_year, revenue, free_cash_flow,
            shares_outstanding, net_debt, cash
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            revenue = VALUES(revenue),
            free_cash_flow = VALUES(free_cash_flow),
            shares_outstanding = VALUES(shares_outstanding),
            net_debt = VALUES(net_debt),
            cash = VALUES(cash)
    """

    count = 0
    for row in rows:
        cursor.execute(
            upsert_sql,
            (
                ticker,
                int(row.get("fiscal_year", 0)),
                float(row.get("revenue", 0.0)),
                float(row.get("free_cash_flow", 0.0)),
                float(row.get("shares_outstanding", 1.0)),
                float(row.get("net_debt", 0.0)),
                float(row.get("cash", 0.0)),
            ),
        )
        count += 1

    conn.commit()
    cursor.close()
    return count


def _fetch_and_store_missing_fundamentals(ticker: str, conn, min_years: int = 5) -> int:
    """Backfill missing DCF fundamentals from APIs and store in MySQL."""
    rows = _fetch_alpha_vantage_fundamentals(ticker, min_years=min_years)
    source = "alpha_vantage"
    if not rows:
        rows = _fetch_yfinance_fundamentals(ticker, min_years=min_years)
        source = "yfinance"

    inserted = _upsert_fundamentals(conn, ticker, rows)
    if inserted > 0:
        logger.info("Backfilled %s annual fundamental rows for %s via %s", inserted, ticker, source)
    return inserted


def _fetch_and_store_missing_price(ticker: str, conn) -> bool:
    """Backfill missing latest price from APIs and store in prices_latest."""
    price = None

    # Try Alpha Vantage global quote first.
    api_key = (os.getenv("ALPHA_VANTAGE_API_KEY") or "").strip()
    if api_key:
        try:
            resp = requests.get(
                "https://www.alphavantage.co/query",
                params={"function": "GLOBAL_QUOTE", "symbol": ticker, "apikey": api_key},
                timeout=15,
            )
            resp.raise_for_status()
            payload = resp.json()
            price = _safe_float((payload.get("Global Quote") or {}).get("05. price"), 0.0)
            if price <= 0:
                price = None
        except Exception as e:
            logger.warning("Alpha Vantage price fetch failed for %s: %s", ticker, e)

    # yfinance fallback.
    if price is None and YFINANCE_AVAILABLE:
        try:
            tk = yf.Ticker(ticker)
            fast_info = getattr(tk, "fast_info", {}) or {}
            price = _safe_float(fast_info.get("lastPrice"), 0.0)
            if price <= 0:
                hist = tk.history(period="5d")
                if hist is not None and not hist.empty:
                    price = _safe_float(hist["Close"].dropna().iloc[-1], 0.0)
            if price <= 0:
                price = None
        except Exception as e:
            logger.warning("yfinance price fetch failed for %s: %s", ticker, e)

    if price is None:
        return False

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO prices_latest (ticker, price, as_of_date)
        VALUES (%s, %s, CURDATE())
        ON DUPLICATE KEY UPDATE
            price = VALUES(price),
            updated_at = CURRENT_TIMESTAMP
        """,
        (ticker, float(price)),
    )
    conn.commit()
    cursor.close()
    logger.info("Backfilled latest price for %s: %.4f", ticker, price)
    return True


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
            inserted = _fetch_and_store_missing_fundamentals(
                ticker=ticker,
                conn=conn,
                min_years=min_years,
            )
            if inserted > 0:
                df = pd.read_sql(query, conn, params=(ticker, min_years))

        if df.empty:
            raise ValueError(
                f"No fundamentals found for {ticker}. "
                "API backfill from Alpha Vantage/yfinance also returned no usable annual cash flow data."
            )
        
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
            inserted = _fetch_and_store_missing_price(ticker=ticker, conn=conn)
            if inserted:
                cursor = conn.cursor()
                cursor.execute(query, (ticker,))
                row = cursor.fetchone()
                cursor.close()

        if not row:
            raise ValueError(
                f"No current price found for {ticker}. "
                "API backfill from Alpha Vantage/yfinance failed."
            )
        
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
        ensure_dcf_schema(conn)

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
