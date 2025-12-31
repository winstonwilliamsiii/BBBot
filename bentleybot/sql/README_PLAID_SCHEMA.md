# Plaid Integration - SQL Schema Guide

## 📂 File Structure

```
bentleybot/sql/
├── 01_plaid_items_create_table.sql       ← Full schema with 3 tables
├── migrate_plaid_schema.py               ← Auto-migration script
└── #Plaid_MySQL schema per tenant and user.sql  ← Original (reference)
```

## 📋 Tables Created

### 1. **plaid_items** - Bank Connections
Stores Plaid-connected bank accounts with RBAC tenant scoping.

**Key Fields:**
- `tenant_id` (INT) - Multi-tenant support
- `user_id` (INT) - User ownership
- `item_id` (VARCHAR) - Plaid Item ID (unique)
- `access_token` (TEXT) - Long-lived API token
- `institution_name` - Bank name (Chase, BofA, etc.)
- `is_active` - Connection status (1=active, 0=revoked)
- `last_sync` - Last transaction sync timestamp
- `sync_cursor` - Plaid pagination cursor

**Indexes:** 
- `idx_plaid_tenant_user` - Fast RBAC queries
- `idx_plaid_item` - Lookup by item_id
- `idx_plaid_active` - Find active connections
- `UNIQUE tenant_user_item` - One connection per user/institution

---

### 2. **plaid_transactions** - Cached Transactions
Immutable cache of Plaid transactions for fast budget queries.

**Key Fields:**
- `plaid_item_id` (INT) - FK to plaid_items
- `tenant_id` (INT) - Denormalized for fast filtering
- `user_id` (INT) - Denormalized for fast filtering
- `transaction_id` - Plaid transaction ID (unique)
- `amount` - Transaction amount
- `name` - Merchant/description
- `category` - Plaid-enriched category (Shopping, Food, etc.)
- `date` - Posted date
- `pending` - Transaction status

**Indexes:**
- `idx_plaid_trans_user_date` - Find user transactions by date
- `idx_plaid_trans_category` - Category-based aggregation

---

### 3. **plaid_sync_status** - Sync Monitoring
Tracks sync health, errors, and retry status.

**Key Fields:**
- `plaid_item_id` - Which account synced
- `status` - ENUM('success', 'failed', 'in_progress')
- `duration_seconds` - Sync performance
- `error_code` - Plaid error code if failed
- `retry_count` - Number of retry attempts
- `transactions_synced` - Count synced

---

## 🚀 How to Deploy

### Option 1: Auto-Migration Script (Recommended)

```bash
# From project root
python bentleybot/sql/migrate_plaid_schema.py
```

This will:
✅ Auto-detect mansa_bot and mydb from .env
✅ Create tables if missing
✅ Verify all indexes
✅ Show migration summary

### Option 2: Manual SQL Execution

```bash
# Connect to your MySQL database
mysql -u root -p mansa_bot < bentleybot/sql/01_plaid_items_create_table.sql
mysql -u root -p mydb < bentleybot/sql/01_plaid_items_create_table.sql
```

---

## 🔐 RBAC Pattern

All tables follow your existing RBAC model:

```python
# tenant_id = which organization owns the data
# user_id = which user within the org

# Fast queries:
SELECT * FROM plaid_items 
WHERE tenant_id = 1 AND user_id = 123  # One tenant/user
```

**Scoped Queries:**
- `tenant_id` isolation for multi-tenant deployments
- `(tenant_id, user_id)` compound index for fast lookups
- Denormalized `user_id` in transactions table for performance

---

## 🔄 Data Flow

```
Plaid API (Backend)
    ↓
exchange_public_token() [Appwrite Function]
    ↓
INSERT INTO plaid_items (tenant_id, user_id, item_id, access_token)
    ↓
Transaction Sync Service (periodically)
    ↓
INSERT INTO plaid_transactions 
INSERT INTO plaid_sync_status
```

---

## 📊 Query Examples

### Get user's connected banks
```sql
SELECT item_id, institution_name, last_sync, is_active
FROM plaid_items
WHERE tenant_id = 1 AND user_id = 123 AND is_active = 1;
```

### Get recent transactions
```sql
SELECT date, name, amount, category
FROM plaid_transactions
WHERE tenant_id = 1 AND user_id = 123 AND date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
ORDER BY date DESC;
```

### Monitor sync health
```sql
SELECT item_id, status, duration_seconds, error_message, retry_count
FROM plaid_sync_status
WHERE user_id = 123
ORDER BY created_at DESC
LIMIT 10;
```

---

## ⚙️ Environment Variables (for migration script)

```bash
# Primary database (mansa_bot)
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=mansa_bot

# Fallback database (mydb)
BUDGET_MYSQL_HOST=127.0.0.1
BUDGET_MYSQL_PORT=3306
BUDGET_MYSQL_USER=root
BUDGET_MYSQL_PASSWORD=your_password
BUDGET_MYSQL_DATABASE=mydb
```

---

## 🔒 Production Checklist

- [ ] Run migration script: `python bentleybot/sql/migrate_plaid_schema.py`
- [ ] Verify tables exist: `SHOW TABLES LIKE 'plaid%';`
- [ ] Grant permissions: `GRANT ... ON plaid_* TO 'mansa_app'@'localhost';`
- [ ] Test insert: Verify Appwrite Function can write to plaid_items
- [ ] Monitor sync: Check plaid_sync_status table for errors
- [ ] Encrypt tokens: Consider encrypting `access_token` at rest
- [ ] Backup: Regular backups of plaid_items and plaid_transactions

---

## 📝 Notes

1. **Encryption**: `access_token` should be encrypted at rest in production. Consider using MySQL's `AES_ENCRYPT()` or application-level encryption.

2. **Data Retention**: Plaid transactions are immutable. Consider archiving old transactions to separate table for performance.

3. **Sync Cursor**: The `sync_cursor` field enables incremental syncs (only fetch new transactions since last sync).

4. **Soft Deletes**: Use `is_active = 0` instead of hard DELETE to maintain referential integrity.

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| Migration script fails to connect | Check MYSQL_* env variables in .env |
| "Table already exists" error | Tables are already created (safe to ignore) |
| Foreign key constraints | Transactions table doesn't have FK by default (commented out) |
| Missing indexes | Run migration script (it creates indexes) |

---

## 📚 Related Files

- `functions/exchange_public_token/main.py` - Saves tokens to plaid_items
- `frontend/utils/plaid_link.py` - Frontend integration
- `streamlit_app.py` - Appwrite Function calls

---

**Last Updated:** December 31, 2025  
**Status:** ✅ Ready for Production
