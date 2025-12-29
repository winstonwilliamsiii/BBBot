# Database Migrations

This folder contains SQL migration scripts to evolve the database schema over time.

## Migration Files

| File | Description | Date |
|------|-------------|------|
| `001_init.sql` | Initial database setup with core tables | 2025-12-29 |
| `002_add_is_active.sql` | Adds is_active column for soft deletes | 2025-12-29 |
| `003_add_positions_table.sql` | Adds portfolio and broker integration tables | 2025-12-29 |

## How to Apply Migrations

### Option 1: Manual Application (Recommended for First Time)
```bash
# Connect to MySQL
mysql -h 127.0.0.1 -P 3306 -u root -p mydb

# Apply migrations in order
source migrations/001_init.sql;
source migrations/002_add_is_active.sql;
source migrations/003_add_positions_table.sql;
```

### Option 2: Using Script
```bash
# Apply all migrations
python apply_migrations.py

# Apply specific migration
python apply_migrations.py --migration 002_add_is_active.sql
```

## Migration Naming Convention

Migrations follow the format: `NNN_description.sql`

- `NNN` = Sequential number (001, 002, 003...)
- `description` = Brief description using snake_case

## Creating New Migrations

1. **Create new file** with next sequential number
2. **Add header comment** with description and date
3. **Use IF NOT EXISTS** for CREATE statements
4. **Use IF EXISTS** for ALTER statements when possible
5. **Add indexes** for foreign keys and frequently queried columns
6. **Test locally** before committing

### Example Template:
```sql
-- Migration NNN: Brief Description
-- Description: Detailed explanation of what this migration does
-- Date: YYYY-MM-DD

CREATE TABLE IF NOT EXISTS new_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- columns here
    INDEX idx_column (column)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE existing_table
ADD COLUMN IF NOT EXISTS new_column VARCHAR(255);
```

## Migration History

### 001_init.sql
Creates core tables:
- `users` - User accounts with RBAC roles
- `transactions` - Financial transactions from Plaid
- `budgets` - User budget allocations
- `categories` - Transaction categories
- `accounts` - Financial accounts
- `user_plaid_tokens` - Plaid API tokens (legacy)

### 002_add_is_active.sql
Adds `is_active` column to:
- `transactions` (soft delete transactions)
- `budgets` (disable budgets without deleting)
- `accounts` (deactivate accounts)
- Updates `users.is_active` with better documentation

### 003_add_positions_table.sql
Creates investment and broker tables:
- `portfolio_positions` - Investment holdings
- `broker_api_credentials` - API credentials for all brokers
- `broker_connections` - Broker connection tracking
- `plaid_items` - Plaid items (new structure)
- `wefolio_funds` - Webull WeFolio funds

Supported brokers:
- Webull (equities, ETFs, funds)
- IBKR (FOREX, futures, commodities)
- Binance (crypto)
- NinjaTrader (options, futures, FOREX)
- tZero (security tokens)
- MetaTrader 5 (options, futures, FOREX)

## Best Practices

1. **Never modify existing migrations** - Create new migration instead
2. **Always backup database** before applying migrations
3. **Test on local first**, then staging, then production
4. **Keep migrations idempotent** - Safe to run multiple times
5. **Document breaking changes** in migration comments
6. **Version control** - Commit migrations to Git

## Rollback Strategy

Currently migrations don't include rollback scripts. If needed:

1. **Backup database** before migration
2. **Restore from backup** if migration fails
3. **Create reverse migration** if schema change needed

## Database Comparison

After applying migrations, verify schema consistency:

```bash
# Compare local vs production
python compare_mysql_railway_schemas.py

# Compare all databases
python compare_all_databases.py
```

## Related Files

- `create_broker_api_tables.py` - Automated broker table creation
- `compare_all_databases.py` - Schema comparison tool
- `docs/SCHEMA_COMPARISON_GUIDE.md` - Schema comparison documentation
- `docs/BROKER_API_STATUS.md` - Broker integration status

---

*Last updated: December 29, 2025*
