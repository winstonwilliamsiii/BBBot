const { createClient } = require('./_shared/appwriteClient');

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
        const { bot_id, metric_types = [] } = body;

        if (!bot_id) {
            return res.json({ error: 'Missing bot_id' }, 400);
        }

        const result = await databases.listDocuments(
            databaseId,
            'bot_metrics',
            [
                `equal("bot_id", ["${bot_id}"])`,
                `orderDesc("timestamp")`,
                `limit(1000)`
            ]
        );

        // Calculate statistics per metric type
        const stats = {};
        
        result.documents.forEach(doc => {
            const type = doc.metric_type;
            if (!stats[type]) {
                stats[type] = {
                    count: 0,
                    sum: 0,
                    min: Infinity,
                    max: -Infinity,
                    avg: 0,
                    latest: null,
                    latest_timestamp: null
                };
            }
            
            const value = parseFloat(doc.metric_value);
            stats[type].count++;
            stats[type].sum += value;
            stats[type].min = Math.min(stats[type].min, value);
            stats[type].max = Math.max(stats[type].max, value);
            
            // Track latest value
            if (!stats[type].latest_timestamp || doc.timestamp > stats[type].latest_timestamp) {
                stats[type].latest = value;
                stats[type].latest_timestamp = doc.timestamp;
            }
        });

        // Calculate averages
        Object.keys(stats).forEach(type => {
            stats[type].avg = stats[type].sum / stats[type].count;
        });

        return res.json({ 
            success: true, 
            bot_id,
            statistics: stats,
            total_metrics: result.documents.length,
            message: `Retrieved statistics for bot ${bot_id}`
        }, 200);
    } catch (err) {
        console.error('get_bot_metrics_stats error:', err);
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
