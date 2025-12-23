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
        const { user_id, limit = 100 } = body;

        if (!user_id) {
            return res.json({ error: 'Missing user_id' }, 400);
        }

        const result = await databases.listDocuments(
            databaseId,
            'transactions',
            [
                `equal("user_id", ["${user_id}"])`,
                `orderDesc("date")`,
                `limit(${limit})`
            ]
        );

        return res.json({ success: true, transactions: result.documents }, 200);
    } catch (err) {
        console.error('get_transactions error:', err);
        return res.json({ error: 'Internal server error' }, 500);
    }
};

/**
 * UTILITY: Create Transaction Indexes (Run once during setup)
 * Uncomment and run separately to create indexes in your database
 */
/*
async function createTransactionIndexes() {
    try {
        const { databases } = createClient({
            endpoint: process.env.APPWRITE_FUNCTION_ENDPOINT,
            projectId: process.env.APPWRITE_FUNCTION_PROJECT_ID,
            apiKey: process.env.APPWRITE_API_KEY
        });

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'transactions',
            'idx_transactions_user_date',
            'key',
            ['user_id', 'date'],
            ['ASC', 'DESC']
        );

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'transactions',
            'idx_transactions_user_created',
            'key',
            ['user_id', 'created_at'],
            ['ASC', 'DESC']
        );

        console.log('✅ Transaction indexes created');
    } catch (error) {
        console.error('❌ Error creating transaction indexes:', error);
    }
}
*/
