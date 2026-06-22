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
        const { user_id } = body;

        if (!user_id) {
            return res.json({ error: 'Missing user_id' }, 400);
        }

        const result = await databases.listDocuments(
            databaseId,
            'watchlist',
            [
                `equal("user_id", ["${user_id}"])`,
                `orderDesc("added_at")`
            ]
        );

        return res.json({ success: true, watchlist: result.documents }, 200);
    } catch (err) {
        console.error('get_watchlist error:', err);
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
