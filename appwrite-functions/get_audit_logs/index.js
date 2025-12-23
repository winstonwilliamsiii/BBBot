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
        const { userId, limit = 50 } = body;

        if (!userId) {
            return res.json({ error: 'Missing userId' }, 400);
        }

        const result = await databases.listDocuments(
            databaseId,
            'auditlogs',
            [
                `equal("userId", [${parseInt(userId)}])`,
                `orderDesc("actionDate")`,
                `limit(${limit})`
            ]
        );

        return res.json({ success: true, audit_logs: result.documents }, 200);
    } catch (err) {
        console.error('get_audit_logs error:', err);
        return res.json({ error: 'Internal server error' }, 500);
    }
};

/**
 * UTILITY: Create Audit Log Indexes (Run once during setup)
 * Uncomment and run separately to create indexes in your database
 */
/*
async function createAuditLogIndexes() {
    try {
        const { databases } = createClient({
            endpoint: process.env.APPWRITE_FUNCTION_ENDPOINT,
            projectId: process.env.APPWRITE_FUNCTION_PROJECT_ID,
            apiKey: process.env.APPWRITE_API_KEY
        });

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'auditlogs',
            'idx_auditlogs_userId',
            'key',
            ['userId'],
            ['ASC']
        );

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'auditlogs',
            'idx_auditlogs_actionDate',
            'key',
            ['actionDate'],
            ['DESC']
        );

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'auditlogs',
            'idx_auditlogs_userId_actionDate',
            'key',
            ['userId', 'actionDate'],
            ['ASC', 'DESC']
        );

        console.log('✅ Audit log indexes created');
    } catch (error) {
        console.error('❌ Error creating audit log indexes:', error);
    }
}
*/
