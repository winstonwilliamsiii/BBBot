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
        const { user_id, symbol } = body;

        if (!user_id || !symbol) {
            return res.json({ error: 'Missing user_id or symbol' }, 400);
        }

        const now = new Date().toISOString();

        const doc = await databases.createDocument(
            databaseId,
            'watchlist',
            ID.unique(),
            { user_id, symbol, added_at: now }
        );

        return res.json({ success: true, watchlist_item: doc }, 201);
    } catch (err) {
        console.error('add_to_watchlist error:', err);
        return res.json({ error: 'Internal server error' }, 500);
    }
};

/**
 * UTILITY: Create Watchlist Indexes (Run once during setup)
 * Uncomment and run separately to create indexes in your database
 */
/*
async function createWatchlistIndexes() {
    try {
        const { databases } = createClient({
            endpoint: process.env.APPWRITE_FUNCTION_ENDPOINT,
            projectId: process.env.APPWRITE_FUNCTION_PROJECT_ID,
            apiKey: process.env.APPWRITE_API_KEY
        });

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'watchlist',
            'idx_watchlist_user_id',
            'key',
            ['user_id'],
            ['ASC']
        );

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'watchlist',
            'idx_watchlist_symbol',
            'key',
            ['symbol'],
            ['ASC']
        );

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'watchlist',
            'idx_watchlist_user_symbol',
            'key',
            ['user_id', 'symbol'],
            ['ASC', 'ASC']
        );

        console.log('✅ Watchlist indexes created');
    } catch (error) {
        console.error('❌ Error creating watchlist indexes:', error);
    }
}
*/
