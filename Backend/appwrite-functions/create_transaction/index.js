const { createClient } = require('./_shared/appwriteClient');
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
        const { requester_id, user_id, amount, description = '', date } = body;

        if (!requester_id || !user_id || !amount) {
            return res.json({ error: 'Missing required fields: requester_id, user_id, amount' }, 400);
        }

        // RBAC Authorization Check
        try {
            // Get requester role
            const userResponse = await databases.listDocuments(
                databaseId,
                'users',
                [`equal("userId", [${parseInt(requester_id)}])`]
            );
            
            if (userResponse.documents.length === 0) {
                return res.json({ error: 'Requester not found' }, 404);
            }
            
            const requesterRole = userResponse.documents[0].role;
            
            // Admin can create for anyone, users only for themselves
            if (requesterRole !== 'admin' && requester_id !== user_id) {
                return res.json({ error: 'Unauthorized: Insufficient permissions' }, 403);
            }
        } catch (authError) {
            console.error('Authorization error:', authError);
            return res.json({ error: 'Authorization failed' }, 403);
        }

        const now = new Date().toISOString();
        const transactionDate = date || now;

        const tx = await databases.createDocument(
            databaseId,
            'transactions',
            ID.unique(),
            {
                user_id,
                amount: parseFloat(amount),
                description,
                date: transactionDate,
                created_at: now,
                updated_at: now
            }
        );

        // Create audit log
        await databases.createDocument(
            databaseId,
            'auditlogs',
            ID.unique(),
            {
                userId: parseInt(requester_id),
                action: 'CREATE_TRANSACTION',
                actionDate: now,
                actionDescription: `Created transaction for user ${user_id}: $${amount}`,
                ipAddress: req.headers['x-forwarded-for'] || req.headers['remote-addr'] || '',
                userAgent: req.headers['user-agent'] || ''
            }
        );

        return res.json({ 
            success: true, 
            transaction: tx,
            message: `Transaction created successfully for user ${user_id}`
        }, 201);
    } catch (err) {
        console.error('create_transaction error:', err);
        return res.json({ error: 'Internal server error', details: err.message }, 500);
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
