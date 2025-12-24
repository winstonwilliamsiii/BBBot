# Snowflake + Airbyte Connection Guide

## Current Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Your Local System                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐        ┌──────────────┐                  │
│  │   Airbyte    │───────▶│    MySQL     │                  │
│  │ (port 8000)  │        │ (port 3307)  │                  │
│  └──────────────┘        └──────────────┘                  │
│         │                      │                            │
│         │                 Databases:                        │
│         │                 - bbbot1                          │
│         │                 - mansa_bot                       │
│         │                 - MARKET_DATA (needs creation)    │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────┐                  │
│  │      Snowflake (Cloud Service)       │                  │
│  │                                      │                  │
│  │  Needs to be created:                │                  │
│  │  - Account (signup required)         │                  │
│  │  - Database: MARKET_DATA             │                  │
│  │  - Warehouse: AIRBYTE_WH             │                  │
│  │  - User: AIRBYTE_USER                │                  │
│  └──────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## What You Need to Do:

### Option 1: Stay with MySQL (Recommended for Now)
Your quantum stock data is already working in MySQL:
- ✅ Database: `bbbot1`
- ✅ Table: `stock_prices_yf`
- ✅ Data: 2 years of RGTI, QBTS, IONQ, SOUN
- ✅ Accessible via MySQL Workbench

**No additional setup needed!**

### Option 2: Add Snowflake (Advanced Analytics)

#### Step 1: Create Snowflake Account
1. Go to: https://signup.snowflake.com/
2. Sign up (30-day free trial, $400 credits)
3. Choose cloud provider: **AWS** (recommended)
4. Choose region: **US East (Virginia)** or closest to you
5. Verify your email and log in

#### Step 2: Get Your Account Identifier
After logging in, look at your URL:
```
https://app.snowflake.com/ABC12345/us-east-1/
         └──────────┘  └────────┘
         Account ID    Region
```
Your host will be: `ABC12345.us-east-1.snowflakecomputing.com`

#### Step 3: Run Setup SQL in Snowflake
Click "Worksheets" in Snowflake UI, then run:

```sql
-- 1. Create warehouse (compute resources)
CREATE WAREHOUSE IF NOT EXISTS AIRBYTE_WH 
  WITH WAREHOUSE_SIZE = 'XSMALL' 
  AUTO_SUSPEND = 60 
  AUTO_RESUME = TRUE
  COMMENT = 'Warehouse for Airbyte data loads';

-- 2. Create database
CREATE DATABASE IF NOT EXISTS MARKET_DATA
  COMMENT = 'Database for market and trading data';

-- 3. Use the database
USE DATABASE MARKET_DATA;

-- 4. Create schema (PUBLIC is default)
CREATE SCHEMA IF NOT EXISTS PUBLIC;

-- 5. Create user for Airbyte
CREATE USER IF NOT EXISTS AIRBYTE_USER 
  PASSWORD = 'ChangeThisPassword123!' 
  DEFAULT_ROLE = SYSADMIN
  DEFAULT_WAREHOUSE = AIRBYTE_WH
  COMMENT = 'Service account for Airbyte connections';

-- 6. Grant permissions to user
GRANT ROLE SYSADMIN TO USER AIRBYTE_USER;
GRANT USAGE ON WAREHOUSE AIRBYTE_WH TO ROLE SYSADMIN;
GRANT ALL ON DATABASE MARKET_DATA TO ROLE SYSADMIN;
GRANT ALL ON SCHEMA MARKET_DATA.PUBLIC TO ROLE SYSADMIN;

-- 7. Verify setup
SHOW WAREHOUSES;
SHOW DATABASES;
SHOW USERS LIKE 'AIRBYTE_USER';
```

#### Step 4: Configure Airbyte Connection
In Airbyte UI (http://localhost:8000):

1. **Destinations** → **+ New Destination**
2. Select **Snowflake**
3. Fill in these EXACT values:

| Field | Value | Example |
|-------|-------|---------|
| **Host** | `your_account.region.snowflakecomputing.com` | `ABC12345.us-east-1.snowflakecomputing.com` |
| **Role** | `SYSADMIN` | `SYSADMIN` |
| **Warehouse** | `AIRBYTE_WH` | `AIRBYTE_WH` |
| **Database** | `MARKET_DATA` | `MARKET_DATA` |
| **Schema** | `PUBLIC` | `PUBLIC` |
| **Username** | `AIRBYTE_USER` | `AIRBYTE_USER` |
| **Password** | (from Step 3) | `ChangeThisPassword123!` |

4. Click **Test Connection**
5. If successful, click **Set up destination**

## Common Errors and Fixes:

### Error: "Database 'BBBOT1' does not exist"
**Cause**: Using MySQL database name in Snowflake connection
**Fix**: Use `MARKET_DATA` as the database name in Airbyte

### Error: "Account not found"
**Cause**: Wrong host format
**Fix**: Must be `account.region.snowflakecomputing.com` (not just account name)

### Error: "User not authorized"
**Cause**: User doesn't have permissions or wrong password
**Fix**: Re-run the GRANT commands in Step 3

### Error: "Warehouse does not exist"
**Cause**: Warehouse name misspelled or not created
**Fix**: Run the CREATE WAREHOUSE command again

## Testing the Connection:

After setup, test with this query in Snowflake:
```sql
USE WAREHOUSE AIRBYTE_WH;
USE DATABASE MARKET_DATA;
USE SCHEMA PUBLIC;

-- This should work if setup is correct
SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE();
```

## Next Steps After Connection:

1. **Create a Source** in Airbyte (e.g., MySQL)
2. **Create a Connection** between MySQL source and Snowflake destination
3. **Configure sync** to move your quantum stock data from MySQL to Snowflake
4. **Run sync** and verify data appears in Snowflake

## Why Use Both MySQL and Snowflake?

| Feature | MySQL | Snowflake |
|---------|-------|-----------|
| **Purpose** | Operational data, real-time | Analytics, reporting, ML |
| **Cost** | Free (self-hosted) | Pay per use (~$2-5/day for small loads) |
| **Speed** | Fast for small queries | Fast for massive datasets |
| **Scaling** | Limited by server | Unlimited |
| **Best For** | Daily trading data | Historical analysis, backtesting |

Your current setup (MySQL only) is perfect for getting started!
