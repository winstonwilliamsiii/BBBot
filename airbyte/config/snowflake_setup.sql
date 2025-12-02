-- ============================================================================
-- Snowflake Setup Script for BentleyBot
-- Run this in Snowflake Worksheets after logging in
-- ============================================================================

-- IMPORTANT: Make sure you're using ACCOUNTADMIN role
USE ROLE ACCOUNTADMIN;

-- Step 1: Create Warehouse (Compute Resources)
CREATE WAREHOUSE IF NOT EXISTS AIRBYTE_WH 
  WITH 
    WAREHOUSE_SIZE = 'XSMALL'           -- Smallest/cheapest size (~$2/hour when running)
    AUTO_SUSPEND = 60                   -- Auto-pause after 1 minute of inactivity
    AUTO_RESUME = TRUE                  -- Auto-start when query runs
    INITIALLY_SUSPENDED = TRUE          -- Start in suspended state (no charges)
    COMMENT = 'Warehouse for Airbyte data ingestion and analysis';

-- Verify warehouse was created
SHOW WAREHOUSES LIKE 'AIRBYTE_WH';

-- ============================================================================

-- Step 2: Create Database for Market Data
CREATE DATABASE IF NOT EXISTS MARKET_DATA
  COMMENT = 'Database for all market data from various sources';

-- Switch to the new database
USE DATABASE MARKET_DATA;

-- Verify database was created
SHOW DATABASES LIKE 'MARKET_DATA';

-- ============================================================================

-- Step 3: Create Schemas for Data Organization
-- Each schema represents a different data source

-- Schema for yfinance data
CREATE SCHEMA IF NOT EXISTS YFINANCE
  COMMENT = 'Yahoo Finance data (free real-time stock prices)';

-- Schema for Tiingo data  
CREATE SCHEMA IF NOT EXISTS TIINGO
  COMMENT = 'Tiingo API data (premium historical stock prices)';

-- Schema for future data sources
CREATE SCHEMA IF NOT EXISTS STOCKTWITS
  COMMENT = 'StockTwits sentiment data';

CREATE SCHEMA IF NOT EXISTS POLYGON
  COMMENT = 'Polygon.io market data';

CREATE SCHEMA IF NOT EXISTS BARCHART
  COMMENT = 'Barchart futures and options data';

-- Schema for your custom analytics
CREATE SCHEMA IF NOT EXISTS ANALYTICS
  COMMENT = 'Custom analysis, aggregations, and ML features';

-- Keep PUBLIC schema for testing
-- It's created by default, so just add a comment
COMMENT ON SCHEMA PUBLIC IS 'Default schema for testing and ad-hoc queries';

-- Verify schemas were created
SHOW SCHEMAS IN DATABASE MARKET_DATA;

-- ============================================================================

-- Step 4: Create Service User for Airbyte
-- Note: Since you're the only user, you can use your own account for Airbyte too
-- But we'll create this user for best practices
CREATE USER IF NOT EXISTS AIRBYTE_USER
  PASSWORD = 'BentleyBot2025!Secure'     -- CHANGE THIS PASSWORD!
  DEFAULT_ROLE = ACCOUNTADMIN            -- Changed to ACCOUNTADMIN since you're sole user
  DEFAULT_WAREHOUSE = AIRBYTE_WH
  DEFAULT_NAMESPACE = 'MARKET_DATA.PUBLIC'
  MUST_CHANGE_PASSWORD = FALSE           -- Set to TRUE for production
  COMMENT = 'Service account for Airbyte connections';

-- Verify user was created
SHOW USERS LIKE 'AIRBYTE_USER';

-- ============================================================================

-- Step 5: Grant Permissions to AIRBYTE_USER

-- Grant ACCOUNTADMIN role to user (since you're sole user, this is safe)
GRANT ROLE ACCOUNTADMIN TO USER AIRBYTE_USER;

-- Also grant SYSADMIN for flexibility
GRANT ROLE SYSADMIN TO USER AIRBYTE_USER;

-- Grant warehouse usage to both roles
GRANT USAGE ON WAREHOUSE AIRBYTE_WH TO ROLE ACCOUNTADMIN;
GRANT OPERATE ON WAREHOUSE AIRBYTE_WH TO ROLE ACCOUNTADMIN;
GRANT USAGE ON WAREHOUSE AIRBYTE_WH TO ROLE SYSADMIN;
GRANT OPERATE ON WAREHOUSE AIRBYTE_WH TO ROLE SYSADMIN;

-- Grant database permissions to both roles
GRANT ALL PRIVILEGES ON DATABASE MARKET_DATA TO ROLE ACCOUNTADMIN;
GRANT ALL PRIVILEGES ON DATABASE MARKET_DATA TO ROLE SYSADMIN;

-- Grant schema permissions (current and future) to both roles
GRANT ALL PRIVILEGES ON ALL SCHEMAS IN DATABASE MARKET_DATA TO ROLE ACCOUNTADMIN;
GRANT ALL PRIVILEGES ON FUTURE SCHEMAS IN DATABASE MARKET_DATA TO ROLE ACCOUNTADMIN;
GRANT ALL PRIVILEGES ON ALL SCHEMAS IN DATABASE MARKET_DATA TO ROLE SYSADMIN;
GRANT ALL PRIVILEGES ON FUTURE SCHEMAS IN DATABASE MARKET_DATA TO ROLE SYSADMIN;

-- Grant table permissions (current and future) to both roles
GRANT ALL PRIVILEGES ON ALL TABLES IN DATABASE MARKET_DATA TO ROLE ACCOUNTADMIN;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN DATABASE MARKET_DATA TO ROLE ACCOUNTADMIN;
GRANT ALL PRIVILEGES ON ALL TABLES IN DATABASE MARKET_DATA TO ROLE SYSADMIN;
GRANT ALL PRIVILEGES ON FUTURE TABLES IN DATABASE MARKET_DATA TO ROLE SYSADMIN;

-- Grant view permissions (current and future) to both roles
GRANT ALL PRIVILEGES ON ALL VIEWS IN DATABASE MARKET_DATA TO ROLE ACCOUNTADMIN;
GRANT ALL PRIVILEGES ON FUTURE VIEWS IN DATABASE MARKET_DATA TO ROLE ACCOUNTADMIN;
GRANT ALL PRIVILEGES ON ALL VIEWS IN DATABASE MARKET_DATA TO ROLE SYSADMIN;
GRANT ALL PRIVILEGES ON FUTURE VIEWS IN DATABASE MARKET_DATA TO ROLE SYSADMIN;

-- ============================================================================

-- Step 6: Test the Setup
-- Stay in ACCOUNTADMIN role for testing

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE AIRBYTE_WH;
USE DATABASE MARKET_DATA;
USE SCHEMA PUBLIC;

-- Verify current context
SELECT 
    CURRENT_USER() as current_user,
    CURRENT_ROLE() as current_role,
    CURRENT_WAREHOUSE() as current_warehouse,
    CURRENT_DATABASE() as current_database,
    CURRENT_SCHEMA() as current_schema;

-- Test table creation (verify write permissions)
CREATE OR REPLACE TABLE MARKET_DATA.PUBLIC.connection_test (
    test_id INT,
    test_message STRING,
    test_timestamp TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Insert test data
INSERT INTO MARKET_DATA.PUBLIC.connection_test (test_id, test_message)
VALUES (1, 'Snowflake connection successful!');

-- Query test data
SELECT * FROM MARKET_DATA.PUBLIC.connection_test;

-- Clean up test table (optional)
-- DROP TABLE MARKET_DATA.PUBLIC.connection_test;

-- ============================================================================

-- Step 7: Get Your Account Identifier
-- Run this to get the exact host name for Airbyte connection

SELECT 
    CURRENT_ACCOUNT() as account_identifier,
    CURRENT_REGION() as region,
    CONCAT(CURRENT_ACCOUNT(), '.', CURRENT_REGION(), '.snowflakecomputing.com') as full_host_name;

-- Copy the "full_host_name" value - you'll need it for Airbyte!

-- ============================================================================
-- SETUP COMPLETE!
-- ============================================================================

-- Summary of what was created:
SHOW WAREHOUSES;
SHOW DATABASES;
SHOW SCHEMAS IN DATABASE MARKET_DATA;
SHOW USERS LIKE 'AIRBYTE_USER';

-- ============================================================================
-- NEXT STEPS:
-- ============================================================================
-- 1. Copy the "full_host_name" from Step 7 results
-- 2. Go to Airbyte UI: http://localhost:8000
-- 3. Create new Snowflake destination with these details:
--    - Host: [value from Step 7]
--    - Role: ACCOUNTADMIN (since you're the sole user)
--    - Warehouse: AIRBYTE_WH
--    - Database: MARKET_DATA
--    - Schema: PUBLIC (or YFINANCE, TIINGO, etc.)
--    - Username: AIRBYTE_USER
--    - Password: BentleyBot2025!Secure (or what you changed it to)
-- 4. Test connection in Airbyte
-- 5. Create your first sync!
-- ============================================================================

-- ============================================================================
-- OPTIONAL: Cost Monitoring Queries
-- ============================================================================

-- Simple warehouse status check (works for all users)
SHOW WAREHOUSES LIKE 'AIRBYTE_WH';

-- Advanced cost monitoring (requires ACCOUNTADMIN role - skip if you get permission error)
-- To use this, you need to: USE ROLE ACCOUNTADMIN; first
-- Uncomment and run separately if needed:
/*
USE ROLE ACCOUNTADMIN;
SELECT 
    WAREHOUSE_NAME,
    SUM(CREDITS_USED) as total_credits,
    SUM(CREDITS_USED) * 3 as estimated_cost_usd  -- Approximate: $3 per credit
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE WAREHOUSE_NAME = 'AIRBYTE_WH'
  AND START_TIME >= DATEADD(day, -7, CURRENT_TIMESTAMP())
GROUP BY WAREHOUSE_NAME;
*/
-- Quick verification
SHOW WAREHOUSES LIKE 'AIRBYTE_WH';
SHOW DATABASES LIKE 'MARKET_DATA';
SHOW SCHEMAS IN DATABASE MARKET_DATA;
SHOW USERS LIKE 'AIRBYTE_USER';

-- Get your connection URL (IMPORTANT - save this!)
SELECT 
    CURRENT_ACCOUNT() as account_identifier,
    CURRENT_REGION() as region,
    CONCAT(CURRENT_ACCOUNT(), '.', CURRENT_REGION(), '.snowflakecomputing.com') as full_host_name;

-- ============================================================================
