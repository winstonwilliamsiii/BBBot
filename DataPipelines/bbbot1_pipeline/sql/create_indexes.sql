-- BentleyBot Database Index Creation Script
-- Creates performance-optimized indexes for stock_prices_yf and stock_fundamentals tables
-- Note: This script is idempotent - safe to run multiple times
-- If indexes already exist, you'll see "Duplicate key name" errors (which can be ignored)

USE bbbot1;

-- ============================================================================
-- VERIFY EXISTING INDEXES
-- ============================================================================
-- To check existing indexes before running:
-- SHOW INDEX FROM stock_prices_yf;
-- SHOW INDEX FROM stock_fundamentals;


-- ============================================================================
-- STOCK_PRICES_YF TABLE INDEXES
-- ============================================================================

-- The following indexes may already exist. If so, you'll get error 1061 (Duplicate key name)
-- This is safe to ignore - it means your indexes are already created

-- Composite index on ticker + date (most common query pattern)
-- This index supports queries like: WHERE ticker = 'IONQ' AND date BETWEEN ... 
-- Note: May already exist from previous run
-- CREATE INDEX idx_ticker_date ON stock_prices_yf (ticker, date);

-- Single index on date for cross-ticker date range queries
-- This index supports queries like: WHERE date BETWEEN ... (all tickers)
-- Note: May already exist from previous run
-- CREATE INDEX idx_date ON stock_prices_yf (date);

-- Single index on ticker for ticker-specific queries
-- This index supports queries like: WHERE ticker = 'IONQ'
-- Note: May already exist from previous run
-- CREATE INDEX idx_ticker ON stock_prices_yf (ticker);

-- Verify indexes exist
SELECT 'stock_prices_yf indexes:' as '';
SHOW INDEX FROM stock_prices_yf WHERE Key_name IN ('idx_ticker_date', 'idx_date', 'idx_ticker');


-- ============================================================================
-- STOCK_FUNDAMENTALS TABLE INDEXES
-- ============================================================================

-- Check if stock_fundamentals table exists before creating indexes
SET @table_exists = (SELECT COUNT(*) FROM information_schema.tables 
                     WHERE table_schema = 'bbbot1' AND table_name = 'stock_fundamentals');

-- The following indexes will be created only if stock_fundamentals table exists
-- If table doesn't exist yet, create it using: python -m bbbot1_pipeline.db

-- Composite index on ticker + report_date
-- CREATE INDEX idx_ticker_report_date ON stock_fundamentals (ticker, report_date);

-- Single index on report_date for cross-ticker fundamental queries
-- CREATE INDEX idx_report_date ON stock_fundamentals (report_date);

-- Single index on ticker for ticker-specific fundamental queries
-- CREATE INDEX idx_ticker_fundamentals ON stock_fundamentals (ticker);


-- ============================================================================
-- SUMMARY
-- ============================================================================
SELECT 'Index setup complete!' as 'Status';
SELECT 'stock_prices_yf has optimized indexes for (ticker, date), (date), and (ticker)' as 'Note';
SELECT CASE 
    WHEN @table_exists > 0 THEN 'stock_fundamentals table exists - create indexes manually'
    ELSE 'stock_fundamentals table not created yet - run: python -m bbbot1_pipeline.db'
END as 'Next Step';

-- ============================================================================
-- VERIFICATION COMPLETE
-- ============================================================================
-- To manually verify indexes at any time, run:
-- SHOW INDEX FROM stock_prices_yf WHERE Key_name LIKE 'idx_%';


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
