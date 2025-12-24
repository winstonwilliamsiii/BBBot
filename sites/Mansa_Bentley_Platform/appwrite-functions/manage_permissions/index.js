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
        const { action, role_id, permission } = body;

        if (!action) {
            return res.json({ error: 'Missing action parameter (create or list)' }, 400);
        }

        if (action === 'create') {
            if (!role_id || !permission) {
                return res.json({ error: 'Missing role_id or permission' }, 400);
            }

            const perm = await databases.createDocument(
                databaseId,
                'permissions',
                ID.unique(),
                { role_id, permission }
            );

            return res.json({ success: true, permission: perm }, 201);
        } else if (action === 'list') {
            if (!role_id) {
                return res.json({ error: 'Missing role_id for listing permissions' }, 400);
            }

            const result = await databases.listDocuments(
                databaseId,
                'permissions',
                [
                    `equal("role_id", ["${role_id}"])`,
                    `orderAsc("permission")`
                ]
            );

            return res.json({ success: true, permissions: result.documents }, 200);
        } else {
            return res.json({ error: 'Invalid action. Use "create" or "list"' }, 400);
        }
    } catch (err) {
        console.error('manage_permissions error:', err);
        return res.json({ error: 'Internal server error' }, 500);
    }
};

/**
 * UTILITY: Create Permission Indexes (Run once during setup)
 * Uncomment and run separately to create indexes in your database
 */
/*
async function createPermissionIndexes() {
    try {
        const { databases } = createClient({
            endpoint: process.env.APPWRITE_FUNCTION_ENDPOINT,
            projectId: process.env.APPWRITE_FUNCTION_PROJECT_ID,
            apiKey: process.env.APPWRITE_API_KEY
        });

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'permissions',
            'idx_permissions_role_id',
            'key',
            ['role_id'],
            ['ASC']
        );

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'permissions',
            'idx_permissions_permission',
            'key',
            ['permission'],
            ['ASC']
        );

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'permissions',
            'idx_permissions_role_permission',
            'key',
            ['role_id', 'permission'],
            ['ASC', 'ASC']
        );

        console.log('✅ Permission indexes created');
    } catch (error) {
        console.error('❌ Error creating permission indexes:', error);
    }
}
*/
