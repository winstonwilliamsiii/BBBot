#Plaid_MySQL schema per tenant and user
#the creation of Plaid items table with RBAC fields
CREATE TABLE plaid_items (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- RBAC / Multi-tenant fields
    tenant_id VARCHAR(64) NOT NULL,   -- Which tenant/org owns this item
    user_id   VARCHAR(64) NOT NULL,   -- Which user within tenant

    -- Plaid identifiers
    item_id        VARCHAR(128) NOT NULL,   -- Plaid Item ID
    access_token   VARCHAR(512) NOT NULL,   -- Long-lived Plaid access token
    institution_id VARCHAR(64),             -- Optional: Plaid institution ID

    -- State management
    is_active TINYINT(1) DEFAULT 1,         -- 1 = active, 0 = revoked
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Audit / raw JSON
    raw_json JSON                           -- Store Plaid metadata for debugging
);

-- Indexes for fast RBAC queries
CREATE INDEX idx_plaid_items_tenant_user
    ON plaid_items (tenant_id, user_id);

CREATE INDEX idx_plaid_items_item
    ON plaid_items (item_id);

CREATE INDEX idx_plaid_items_active
    ON plaid_items (tenant_id, is_active);