const { createClient } = require('../_shared/appwriteClient');

/**
 * Utility Function to Create All Database Indexes
 * Run this once after creating all collections to optimize query performance
 * 
 * Usage: Deploy as an Appwrite Function and execute manually
 */

module.exports = async function (req, res) {
    try {
        const { endpoint, projectId, apiKey, databaseId } = {
            endpoint: process.env.APPWRITE_FUNCTION_ENDPOINT,
            projectId: process.env.APPWRITE_FUNCTION_PROJECT_ID,
            apiKey: process.env.APPWRITE_API_KEY,
            databaseId: process.env.APPWRITE_DATABASE_ID
        };

        const { databases } = createClient({ endpoint, projectId, apiKey });

        const results = {
            success: [],
            errors: []
        };

        // Transaction Indexes
        try {
            await databases.createIndex(
                databaseId,
                'transactions',
                'idx_transactions_user_date',
                'key',
                ['user_id', 'date'],
                ['ASC', 'DESC']
            );
            await databases.createIndex(
                databaseId,
                'transactions',
                'idx_transactions_user_created',
                'key',
                ['user_id', 'created_at'],
                ['ASC', 'DESC']
            );
            results.success.push('transactions');
        } catch (error) {
            results.errors.push({ collection: 'transactions', error: error.message });
        }

        // Watchlist Indexes
        try {
            await databases.createIndex(
                databaseId,
                'watchlist',
                'idx_watchlist_user_id',
                'key',
                ['user_id'],
                ['ASC']
            );
            await databases.createIndex(
                databaseId,
                'watchlist',
                'idx_watchlist_symbol',
                'key',
                ['symbol'],
                ['ASC']
            );
            await databases.createIndex(
                databaseId,
                'watchlist',
                'idx_watchlist_user_symbol',
                'key',
                ['user_id', 'symbol'],
                ['ASC', 'ASC']
            );
            results.success.push('watchlist');
        } catch (error) {
            results.errors.push({ collection: 'watchlist', error: error.message });
        }

        // Audit Log Indexes
        try {
            await databases.createIndex(
                databaseId,
                'auditlogs',
                'idx_auditlogs_userId',
                'key',
                ['userId'],
                ['ASC']
            );
            await databases.createIndex(
                databaseId,
                'auditlogs',
                'idx_auditlogs_actionDate',
                'key',
                ['actionDate'],
                ['DESC']
            );
            await databases.createIndex(
                databaseId,
                'auditlogs',
                'idx_auditlogs_userId_actionDate',
                'key',
                ['userId', 'actionDate'],
                ['ASC', 'DESC']
            );
            results.success.push('auditlogs');
        } catch (error) {
            results.errors.push({ collection: 'auditlogs', error: error.message });
        }

        // Payment Indexes
        try {
            await databases.createIndex(
                databaseId,
                'payments',
                'idx_payments_user_id',
                'key',
                ['user_id'],
                ['ASC']
            );
            await databases.createIndex(
                databaseId,
                'payments',
                'idx_payments_created_at',
                'key',
                ['created_at'],
                ['DESC']
            );
            await databases.createIndex(
                databaseId,
                'payments',
                'idx_payments_user_created',
                'key',
                ['user_id', 'created_at'],
                ['ASC', 'DESC']
            );
            results.success.push('payments');
        } catch (error) {
            results.errors.push({ collection: 'payments', error: error.message });
        }

        // Role Indexes
        try {
            await databases.createIndex(
                databaseId,
                'roles',
                'idx_roles_role_name',
                'key',
                ['role_name'],
                ['ASC']
            );
            results.success.push('roles');
        } catch (error) {
            results.errors.push({ collection: 'roles', error: error.message });
        }

        // Permission Indexes
        try {
            await databases.createIndex(
                databaseId,
                'permissions',
                'idx_permissions_role_id',
                'key',
                ['role_id'],
                ['ASC']
            );
            await databases.createIndex(
                databaseId,
                'permissions',
                'idx_permissions_permission',
                'key',
                ['permission'],
                ['ASC']
            );
            await databases.createIndex(
                databaseId,
                'permissions',
                'idx_permissions_role_permission',
                'key',
                ['role_id', 'permission'],
                ['ASC', 'ASC']
            );
            results.success.push('permissions');
        } catch (error) {
            results.errors.push({ collection: 'permissions', error: error.message });
        }

        // Bot Metrics Indexes
        try {
            await databases.createIndex(
                databaseId,
                'bot_metrics',
                'idx_bot_metrics_bot_id',
                'key',
                ['bot_id'],
                ['ASC']
            );
            await databases.createIndex(
                databaseId,
                'bot_metrics',
                'idx_bot_metrics_timestamp',
                'key',
                ['timestamp'],
                ['DESC']
            );
            await databases.createIndex(
                databaseId,
                'bot_metrics',
                'idx_bot_metrics_metric_type',
                'key',
                ['metric_type'],
                ['ASC']
            );
            await databases.createIndex(
                databaseId,
                'bot_metrics',
                'idx_bot_metrics_bot_timestamp',
                'key',
                ['bot_id', 'timestamp'],
                ['ASC', 'DESC']
            );
            await databases.createIndex(
                databaseId,
                'bot_metrics',
                'idx_bot_metrics_bot_type',
                'key',
                ['bot_id', 'metric_type'],
                ['ASC', 'ASC']
            );
            results.success.push('bot_metrics');
        } catch (error) {
            results.errors.push({ collection: 'bot_metrics', error: error.message });
        }

        console.log('✅ Index creation completed');
        console.log('Success:', results.success);
        console.log('Errors:', results.errors);

        return res.json({
            success: true,
            message: 'Index creation completed',
            results: results
        }, 200);

    } catch (err) {
        console.error('create_all_indexes error:', err);
        return res.json({ error: 'Internal server error', details: err.message }, 500);
    }
};
