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
        const { userId, action, actionDescription = '', ipAddress = '', userAgent = '' } = body;

        if (!userId || !action) {
            return res.json({ error: 'Missing userId or action' }, 400);
        }

        const now = new Date().toISOString();

        const log = await databases.createDocument(
            databaseId,
            'auditlogs',
            ID.unique(),
            {
                userId: parseInt(userId),
                action,
                actionDate: now,
                actionDescription,
                ipAddress,
                userAgent
            }
        );

        return res.json({ success: true, audit_log: log }, 201);
    } catch (err) {
        console.error('create_audit_log error:', err);
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
