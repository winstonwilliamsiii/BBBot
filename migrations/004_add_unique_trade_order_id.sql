-- Migration 004: enforce unique order IDs for broker trade sync dedupe
-- Date: 2026-03-25
-- Purpose: prevent duplicate broker-order ingestion into trades_history

-- Remove duplicate non-empty order IDs, keeping the oldest row.
DELETE t1
FROM trades_history t1
INNER JOIN trades_history t2
    ON t1.order_id = t2.order_id
   AND t1.id > t2.id
WHERE t1.order_id IS NOT NULL
  AND t1.order_id <> '';

-- Add unique index only if it is not already present.
SET @idx_exists := (
    SELECT COUNT(1)
    FROM information_schema.statistics
    WHERE table_schema = DATABASE()
      AND table_name = 'trades_history'
      AND index_name = 'uq_trades_history_order_id'
);

SET @ddl := IF(
    @idx_exists = 0,
    'ALTER TABLE trades_history ADD UNIQUE KEY uq_trades_history_order_id (order_id)',
    'SELECT ''uq_trades_history_order_id already exists'' AS info'
);

PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
