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
        const { user_id, amount } = body;

        if (!user_id || !amount) {
            return res.json({ error: 'Missing user_id or amount' }, 400);
        }

        const now = new Date().toISOString();

        const payment = await databases.createDocument(
            databaseId,
            'payments',
            ID.unique(),
            {
                user_id,
                amount: parseFloat(amount),
                created_at: now
            }
        );

        return res.json({ success: true, payment }, 201);
    } catch (err) {
        console.error('create_payment error:', err);
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
