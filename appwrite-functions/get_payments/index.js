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
        const { user_id, limit = 50 } = body;

        if (!user_id) {
            return res.json({ error: 'Missing user_id' }, 400);
        }

        const result = await databases.listDocuments(
            databaseId,
            'payments',
            [
                `equal("user_id", ["${user_id}"])`,
                `orderDesc("created_at")`,
                `limit(${limit})`
            ]
        );

        return res.json({ success: true, payments: result.documents }, 200);
    } catch (err) {
        console.error('get_payments error:', err);
        return res.json({ error: 'Internal server error' }, 500);
    }
};

/**
 * UTILITY: Create Payment Indexes (Run once during setup)
 * Uncomment and run separately to create indexes in your database
 */
/*
async function createPaymentIndexes() {
    try {
        const { databases } = createClient({
            endpoint: process.env.APPWRITE_FUNCTION_ENDPOINT,
            projectId: process.env.APPWRITE_FUNCTION_PROJECT_ID,
            apiKey: process.env.APPWRITE_API_KEY
        });

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'payments',
            'idx_payments_user_id',
            'key',
            ['user_id'],
            ['ASC']
        );

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'payments',
            'idx_payments_created_at',
            'key',
            ['created_at'],
            ['DESC']
        );

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'payments',
            'idx_payments_user_created',
            'key',
            ['user_id', 'created_at'],
            ['ASC', 'DESC']
        );

        console.log('✅ Payment indexes created');
    } catch (error) {
        console.error('❌ Error creating payment indexes:', error);
    }
}
*/
