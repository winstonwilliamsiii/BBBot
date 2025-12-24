const { createClient } = require('../_shared/appwriteClient');
const { ID } = require('node-appwrite');

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
            metric_type, 
            metric_value, 
            timestamp, 
            metadata = {} 
        } = body;

        if (!bot_id || !metric_type || metric_value === undefined) {
            return res.json({ 
                error: 'Missing required fields: bot_id, metric_type, metric_value' 
            }, 400);
        }

        const now = new Date().toISOString();
        const metricTimestamp = timestamp || now;

        const metric = await databases.createDocument(
            databaseId,
            'bot_metrics',
            ID.unique(),
            {
                bot_id,
                metric_type,
                metric_value: parseFloat(metric_value),
                timestamp: metricTimestamp,
                metadata: JSON.stringify(metadata),
                created_at: now
            }
        );

        return res.json({ 
            success: true, 
            bot_metric: metric,
            message: `Bot metric recorded for bot ${bot_id}`
        }, 201);
    } catch (err) {
        console.error('create_bot_metric error:', err);
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
