const { createClient } = require('../_shared/appwriteClient');

module.exports = async function (req, res) {
    try {
        const { endpoint, projectId, apiKey, databaseId } = {
            endpoint: process.env.APPWRITE_FUNCTION_ENDPOINT,
            projectId: process.env.APPWRITE_FUNCTION_PROJECT_ID,
            apiKey: process.env.APPWRITE_API_KEY,
            databaseId: process.env.APPWRITE_DATABASE_ID
        };

        const { databases } = createClient({ endpoint, projectId, apiKey });

        const body = JSON.parse(req.body || '{}');
        const { 
            bot_id, 
            metric_type = null,
            start_date = null,
            end_date = null,
            limit = 100 
        } = body;

        if (!bot_id) {
            return res.json({ error: 'Missing bot_id' }, 400);
        }

        // Build query filters
        const queries = [`equal("bot_id", ["${bot_id}"])`];
        
        if (metric_type) {
            queries.push(`equal("metric_type", ["${metric_type}"])`);
        }
        
        if (start_date) {
            queries.push(`greaterThanEqual("timestamp", "${start_date}")`);
        }
        
        if (end_date) {
            queries.push(`lessThanEqual("timestamp", "${end_date}")`);
        }
        
        queries.push(`orderDesc("timestamp")`);
        queries.push(`limit(${limit})`);

        const result = await databases.listDocuments(
            databaseId,
            'bot_metrics',
            queries
        );

        return res.json({ 
            success: true, 
            bot_metrics: result.documents,
            total: result.documents.length,
            message: `Retrieved ${result.documents.length} metrics for bot ${bot_id}`
        }, 200);
    } catch (err) {
        console.error('get_bot_metrics error:', err);
        return res.json({ error: 'Internal server error', details: err.message }, 500);
    }
};

/**
 * UTILITY: Create Bot Metrics Indexes (Run once during setup)
 * Uncomment and run separately to create indexes in your database
 */
/*
async function createBotMetricsIndexes() {
    try {
        const { databases } = createClient({
            endpoint: process.env.APPWRITE_FUNCTION_ENDPOINT,
            projectId: process.env.APPWRITE_FUNCTION_PROJECT_ID,
            apiKey: process.env.APPWRITE_API_KEY
        });

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'bot_metrics',
            'idx_bot_metrics_bot_id',
            'key',
            ['bot_id'],
            ['ASC']
        );

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'bot_metrics',
            'idx_bot_metrics_timestamp',
            'key',
            ['timestamp'],
            ['DESC']
        );

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'bot_metrics',
            'idx_bot_metrics_metric_type',
            'key',
            ['metric_type'],
            ['ASC']
        );

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'bot_metrics',
            'idx_bot_metrics_bot_timestamp',
            'key',
            ['bot_id', 'timestamp'],
            ['ASC', 'DESC']
        );

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'bot_metrics',
            'idx_bot_metrics_bot_type',
            'key',
            ['bot_id', 'metric_type'],
            ['ASC', 'ASC']
        );

        console.log('✅ Bot metrics indexes created');
    } catch (error) {
        console.error('❌ Error creating bot metrics indexes:', error);
    }
}
*/
