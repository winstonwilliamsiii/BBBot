-- ============================================
-- DCF ANALYSIS DATABASE SETUP
-- ============================================
-- Database: Bentley_Budget
-- Connection: 127.0.0.1:3306 (root@localhost)
-- ============================================

USE Bentley_Budget;

-- ============================================
-- FUNDAMENTALS ANNUAL TABLE
-- ============================================
-- Stores historical fundamental data for DCF analysis
CREATE TABLE IF NOT EXISTS fundamentals_annual (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    fiscal_year INT NOT NULL,
    revenue DECIMAL(20,2) DEFAULT NULL COMMENT 'Annual revenue in USD',
    free_cash_flow DECIMAL(20,2) DEFAULT NULL COMMENT 'Free cash flow in USD',
    shares_outstanding DECIMAL(20,2) DEFAULT NULL COMMENT 'Shares outstanding (millions)',
    net_debt DECIMAL(20,2) DEFAULT 0 COMMENT 'Total debt minus cash',
    cash DECIMAL(20,2) DEFAULT 0 COMMENT 'Cash and equivalents',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_ticker_year (ticker, fiscal_year),
    INDEX idx_ticker (ticker),
    INDEX idx_fiscal_year (fiscal_year)
) ENGINE=InnoDB COMMENT='Annual fundamental data for DCF valuation';

-- ============================================
-- PRICES LATEST TABLE
-- ============================================
-- Stores most recent market prices for valuation comparison
CREATE TABLE IF NOT EXISTS prices_latest (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    price DECIMAL(12,4) NOT NULL COMMENT 'Current market price',
    as_of_date DATE NOT NULL COMMENT 'Price date',
    volume BIGINT DEFAULT NULL COMMENT 'Trading volume',
    market_cap DECIMAL(20,2) DEFAULT NULL COMMENT 'Market capitalization',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_ticker_date (ticker, as_of_date),
    INDEX idx_ticker (ticker),
    INDEX idx_as_of_date (as_of_date)
) ENGINE=InnoDB COMMENT='Latest market prices for DCF comparison';

-- ============================================
-- SAMPLE DATA - EXAMPLE ENTRIES
-- ============================================
-- Insert sample data for testing (optional)

-- Example: AAPL fundamentals
INSERT IGNORE INTO fundamentals_annual 
    (ticker, fiscal_year, revenue, free_cash_flow, shares_outstanding, net_debt, cash)
VALUES 
    ('AAPL', 2023, 383285000000, 99584000000, 15550.06, -60700000000, 166300000000),
    ('AAPL', 2022, 394328000000, 111443000000, 15908.12, -51700000000, 156200000000),
    ('AAPL', 2021, 365817000000, 92953000000, 16426.79, -85100000000, 130100000000),
    ('AAPL', 2020, 274515000000, 73365000000, 16976.76, -76300000000, 90900000000),
    ('AAPL', 2019, 260174000000, 58896000000, 17772.95, -100700000000, 102900000000);

-- Example: AAPL current price
INSERT IGNORE INTO prices_latest
    (ticker, price, as_of_date, volume, market_cap)
VALUES
    ('AAPL', 189.50, CURDATE(), 50234567, 2946000000000);

-- Example: MSFT fundamentals
INSERT IGNORE INTO fundamentals_annual
    (ticker, fiscal_year, revenue, free_cash_flow, shares_outstanding, net_debt, cash)
VALUES
    ('MSFT', 2023, 211915000000, 65149000000, 7440.51, -18400000000, 136400000000),
    ('MSFT', 2022, 198270000000, 65149000000, 7496.62, -15000000000, 127800000000),
    ('MSFT', 2021, 168088000000, 56118000000, 7547.22, -25000000000, 130300000000),
    ('MSFT', 2020, 143015000000, 45234000000, 7571.55, -33900000000, 136500000000),
    ('MSFT', 2019, 125843000000, 38260000000, 7643.31, -63800000000, 133800000000);

-- Example: MSFT current price
INSERT IGNORE INTO prices_latest
    (ticker, price, as_of_date, volume, market_cap)
VALUES
    ('MSFT', 415.25, CURDATE(), 23456789, 3090000000000);

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check fundamentals data
SELECT 
    ticker,
    COUNT(*) as years_of_data,
    MIN(fiscal_year) as earliest_year,
    MAX(fiscal_year) as latest_year
FROM fundamentals_annual
GROUP BY ticker
ORDER BY ticker;

-- Check prices data
SELECT 
    ticker,
    price,
    as_of_date,
    market_cap / 1000000000 as market_cap_billions
FROM prices_latest
ORDER BY ticker;

-- ============================================
-- USAGE INSTRUCTIONS
-- ============================================
/*
1. Run this script to create tables:
   mysql -h 127.0.0.1 -u root -p Bentley_Budget < setup_dcf_database.sql

2. Verify tables exist:
   SHOW TABLES LIKE '%fundamental%';
   SHOW TABLES LIKE '%prices%';

3. Test DCF analysis with sample data:
   python -c "from frontend.components.dcf_analysis import run_equity_dcf; print(run_equity_dcf('AAPL'))"

4. To add your own stock data:
   - Insert historical fundamentals (minimum 5 years)
   - Insert current price
   - Run DCF analysis via dashboard widget

5. Data sources for populating tables:
   - Yahoo Finance (yfinance library)
   - Alpha Vantage API
   - Financial Modeling Prep API
   - Manual entry from financial statements
*/
