# Airbyte Connection Setup - Primary Key Configuration

## Quick Reference: View Primary Keys in MySQL

### Using MySQL Workbench:
1. Connect to `127.0.0.1:3307` (username: `root`, password: `root`)
2. Expand `bbbot1` database
3. Right-click on table → **Table Inspector** → **Indexes** tab
4. Look for `PRIMARY` key type

### Using Command Line:
```bash
# Show table structure with keys
docker exec bentley-mysql mysql -uroot -proot -e "DESCRIBE bbbot1.stock_prices_yf;"

# Show all indexes including primary keys
docker exec bentley-mysql mysql -uroot -proot -e "SHOW INDEX FROM bbbot1.stock_prices_yf;"

# Show CREATE TABLE statement (includes primary key definition)
docker exec bentley-mysql mysql -uroot -proot -e "SHOW CREATE TABLE bbbot1.stock_prices_yf\G"
```

## Current Configuration

### MySQL Tables (Source)

#### `bbbot1.stock_prices_yf` (yfinance data)
**Primary Key**: `ticker + date` (composite)
- Modified on: December 2, 2025
- Structure:
  - `id` INT AUTO_INCREMENT UNIQUE (kept for reference)
  - `ticker` VARCHAR(10) - Part of PRIMARY KEY
  - `date` DATE - Part of PRIMARY KEY
  - `open`, `high`, `low`, `close`, `volume`, `adj_close` DECIMAL/BIGINT
  - `created_at` TIMESTAMP

**Command used to set primary key:**
```sql
ALTER TABLE bbbot1.stock_prices_yf 
DROP PRIMARY KEY, 
ADD PRIMARY KEY (ticker, date), 
MODIFY id INT AUTO_INCREMENT UNIQUE;
```

#### `bbbot1.stock_prices_tiingo` (Tiingo data)
**Primary Key**: `ticker + date` (composite) - already set in DAG
- Defined in: `airflow/dags/tiingo_data_historical.py`
- Same structure as yfinance table

### Airbyte Source Configuration

**Source: MySQL (bbbot1)**
- Connection: Direct to Docker MySQL container
- Host: `mysql` (internal Docker network) or `127.0.0.1:3307` (from host)
- Database: `bbbot1`
- Tables:
  - `stock_prices_yf` - Yahoo Finance quantum stocks (RGTI, QBTS, IONQ, SOUN)
  - `stock_prices_tiingo` - Tiingo API data (when premium subscription active)

### Airbyte Destination Configuration

**Destination: Snowflake (MARKET_DATA)**
- Host: `[your_account].[region].snowflakecomputing.com`
- Database: `MARKET_DATA`
- Warehouse: `AIRBYTE_WH`
- User: `AIRBYTE_USER`
- Role: `ACCOUNTADMIN`
- Default Schema: `PUBLIC` (can use `YFINANCE`, `TIINGO`, etc.)

### Stream Configuration in Airbyte

**For stock_prices_yf table:**

1. **Primary Key**: 
   - Select: `ticker` AND `date` (composite key)
   - Why: Uniquely identifies each stock price record (one ticker per day)

2. **Cursor Field**: 
   - Select: `date`
   - Why: Enables incremental syncs (only fetch new dates)

3. **Sync Mode**: 
   - Recommended: `Incremental | Append + Deduped`
   - Why: Only syncs new data, prevents duplicates using primary key

4. **Namespace**: 
   - Destination: `YFINANCE` (schema in Snowflake)
   - Why: Organizes data by source

## Modifying Primary Keys Later

### If you need to change the primary key back to `id`:

```bash
docker exec bentley-mysql mysql -uroot -proot -e "
ALTER TABLE bbbot1.stock_prices_yf 
DROP PRIMARY KEY, 
ADD PRIMARY KEY (id),
ADD UNIQUE KEY unique_ticker_date (ticker, date);
"
```

### If you need to add primary key to another table:

```bash
# For stock_prices_tiingo (should already be set from DAG)
docker exec bentley-mysql mysql -uroot -proot -e "
ALTER TABLE bbbot1.stock_prices_tiingo 
ADD PRIMARY KEY (ticker, date);
"
```

### After changing primary keys in MySQL:

1. Go to Airbyte UI: http://localhost:8000
2. Navigate to **Sources** → Your MySQL source
3. Click **Settings** → **Refresh source schema**
4. Wait 30-60 seconds for schema refresh
5. Edit your connection and reconfigure the primary key selection
6. Save and trigger a new sync

## Best Practices

### Primary Key Selection for Stock Data:

✅ **Recommended**: `ticker + date`
- Natural business key
- Prevents duplicate prices for same stock on same day
- Meaningful for analysis
- Easier to debug data issues

❌ **Not Recommended**: `id` only
- Arbitrary surrogate key
- Doesn't prevent logical duplicates (same ticker/date with different IDs)
- Less intuitive for analysts

### Cursor Field Selection:

✅ **Always use**: `date` for stock price data
- Chronological ordering
- Enables efficient incremental syncs
- Aligns with how stock data grows (by date)

### Sync Modes:

| Mode | Use Case | Best For |
|------|----------|----------|
| **Full Refresh \| Overwrite** | Complete replacement | Testing, small datasets |
| **Full Refresh \| Append** | Historical backfills | Initial loads |
| **Incremental \| Append** | Only new records | Growing datasets |
| **Incremental \| Append + Deduped** | New records, update existing | Stock prices (RECOMMENDED) |

## Current Setup Summary

As of December 2, 2025:

### Sources in Airbyte:
1. ✅ MySQL (bbbot1) - Stock price data
2. ✅ Google Sheets - (your additional source)
3. ✅ Yahoo Finance Price - (if using direct connector)

### Destinations in Airbyte:
1. ✅ Snowflake (MARKET_DATA) - Analytics warehouse
2. ✅ Google Sheets - (if configured as destination)

### Active Connections:
- MySQL → Snowflake (stock_prices_yf)
- Status: Connected, primary key configured as `ticker + date`
- Note: Schema refresh not yet performed after primary key change
- **Action Required**: Refresh source schema in Airbyte when comfortable

## Troubleshooting

### "Primary key not found" error:
1. Verify primary key exists in MySQL (use commands above)
2. Refresh source schema in Airbyte
3. If still not showing, check Airbyte logs for MySQL connection issues

### "Sync failed" errors:
1. Check Snowflake warehouse is running (`SHOW WAREHOUSES;`)
2. Verify AIRBYTE_USER has proper permissions
3. Check Airbyte connection logs for specific error

### Duplicate records in Snowflake:
1. Verify primary key is set correctly in Airbyte
2. Use `Append + Deduped` sync mode
3. May need to run a full refresh to clear duplicates

## Next Steps

When you're ready to refresh the schema:

1. **Backup your data** (optional but safe):
   ```bash
   docker exec bentley-mysql mysqldump -uroot -proot bbbot1 stock_prices_yf > backup_yf_$(date +%Y%m%d).sql
   ```

2. **In Airbyte UI**:
   - Sources → MySQL (bbbot1) → Settings
   - Click "Refresh source schema"
   - Wait for completion

3. **Update connection**:
   - Connections → Your MySQL → Snowflake connection
   - Edit stream configuration
   - Set Primary Key to: `ticker`, `date`
   - Set Cursor Field to: `date`
   - Save

4. **Test sync**:
   - Trigger manual sync
   - Check Snowflake for data: `SELECT * FROM MARKET_DATA.PUBLIC.stock_prices_yf LIMIT 10;`

## Reference: Schema Refresh is Safe

Refreshing the source schema in Airbyte:
- ✅ Only updates metadata (column names, types, keys)
- ✅ Does NOT delete data
- ✅ Does NOT modify existing syncs
- ✅ Allows you to reconfigure streams
- ⚠️ May pause running syncs temporarily

Feel confident to refresh when ready!
