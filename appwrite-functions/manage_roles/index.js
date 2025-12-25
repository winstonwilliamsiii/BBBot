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
        const { action, role_name } = body;

        if (!action) {
            return res.json({ error: 'Missing action parameter (create or list)' }, 400);
        }

        if (action === 'create') {
            if (!role_name) {
                return res.json({ error: 'Missing role_name' }, 400);
            }

            const role = await databases.createDocument(
                databaseId,
                'roles',
                ID.unique(),
                { role_name: role_name.toLowerCase() }
            );

            return res.json({ success: true, role }, 201);
        } else if (action === 'list') {
            const result = await databases.listDocuments(
                databaseId,
                'roles',
                [`orderAsc("role_name")`]
            );

            return res.json({ success: true, roles: result.documents }, 200);
        } else {
            return res.json({ error: 'Invalid action. Use "create" or "list"' }, 400);
        }
    } catch (err) {
        console.error('manage_roles error:', err);
        return res.json({ error: 'Internal server error' }, 500);
    }
};

/**
 * UTILITY: Create Role Indexes (Run once during setup)
 * Uncomment and run separately to create indexes in your database
 */
/*
async function createRoleIndexes() {
    try {
        const { databases } = createClient({
            endpoint: process.env.APPWRITE_FUNCTION_ENDPOINT,
            projectId: process.env.APPWRITE_FUNCTION_PROJECT_ID,
            apiKey: process.env.APPWRITE_API_KEY
        });

        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'roles',
            'idx_roles_role_name',
            'key',
            ['role_name'],
            ['ASC']
        );

        console.log('✅ Role indexes created');
    } catch (error) {
        console.error('❌ Error creating role indexes:', error);
    }
}
*/
