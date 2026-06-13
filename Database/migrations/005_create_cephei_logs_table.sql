-- Migration 005: Create Cephei logs table
-- Description: Adds logs table used by cephei_bot.py for runtime event logging
-- Date: 2026-05-05

CREATE TABLE IF NOT EXISTS logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    entry TEXT NOT NULL COMMENT 'Application log entry payload',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
