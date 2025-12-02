-- BentleyBot Database Index Creation Script
-- Creates performance-optimized indexes for stock_prices_yf and stock_fundamentals tables
-- Run this script after initial table creation to improve query performance

USE bbbot1;

-- ============================================================================
-- STOCK_PRICES_YF TABLE INDEXES
-- ============================================================================

-- Composite index on ticker + date (most common query pattern)
-- This index supports queries like: WHERE ticker = 'IONQ' AND date BETWEEN ... 
CREATE INDEX IF NOT EXISTS idx_ticker_date 
ON stock_prices_yf (ticker, date);

-- Single index on date for cross-ticker date range queries
-- This index supports queries like: WHERE date BETWEEN ... (all tickers)
CREATE INDEX IF NOT EXISTS idx_date 
ON stock_prices_yf (date);

-- Single index on ticker for ticker-specific queries
-- This index supports queries like: WHERE ticker = 'IONQ'
CREATE INDEX IF NOT EXISTS idx_ticker 
ON stock_prices_yf (ticker);

-- Note: Primary key (ticker, date) already provides index functionality
-- Additional indexes created for query pattern optimization


-- ============================================================================
-- STOCK_FUNDAMENTALS TABLE INDEXES
-- ============================================================================

-- Composite index on ticker + report_date
-- This index supports queries like: WHERE ticker = 'IONQ' AND report_date BETWEEN ...
CREATE INDEX IF NOT EXISTS idx_ticker_report_date 
ON stock_fundamentals (ticker, report_date);

-- Single index on report_date for cross-ticker fundamental queries
-- This index supports queries like: WHERE report_date BETWEEN ... (all tickers)
CREATE INDEX IF NOT EXISTS idx_report_date 
ON stock_fundamentals (report_date);

-- Single index on ticker for ticker-specific fundamental queries
-- This index supports queries like: WHERE ticker = 'IONQ'
CREATE INDEX IF NOT EXISTS idx_ticker_fundamentals 
ON stock_fundamentals (ticker);


-- ============================================================================
-- VERIFY INDEXES
-- ============================================================================

-- Show all indexes on stock_prices_yf
SHOW INDEX FROM stock_prices_yf;

-- Show all indexes on stock_fundamentals
SHOW INDEX FROM stock_fundamentals;


-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Example 1: Query optimized by idx_ticker_date
-- EXPLAIN SELECT * FROM stock_prices_yf 
-- WHERE ticker = 'IONQ' AND date >= '2024-01-01';

-- Example 2: Query optimized by idx_date
-- EXPLAIN SELECT ticker, AVG(close) 
-- FROM stock_prices_yf 
-- WHERE date >= '2024-01-01' 
-- GROUP BY ticker;

-- Example 3: Query optimized by idx_ticker_report_date
-- EXPLAIN SELECT * FROM stock_fundamentals 
-- WHERE ticker = 'QBTS' AND report_date >= '2024-01-01';


-- ============================================================================
-- INDEX MAINTENANCE
-- ============================================================================

-- To rebuild indexes if needed (rarely necessary in MySQL):
-- ALTER TABLE stock_prices_yf DROP INDEX idx_ticker_date, ADD INDEX idx_ticker_date (ticker, date);

-- To analyze index usage:
-- SHOW INDEX FROM stock_prices_yf WHERE Key_name = 'idx_ticker_date';

-- To check index cardinality and selectivity:
-- SELECT 
--     INDEX_NAME,
--     CARDINALITY,
--     SEQ_IN_INDEX,
--     COLUMN_NAME
-- FROM information_schema.STATISTICS
-- WHERE TABLE_SCHEMA = 'bbbot1' 
--   AND TABLE_NAME IN ('stock_prices_yf', 'stock_fundamentals');
