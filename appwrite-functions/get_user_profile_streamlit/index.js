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
        const { userId } = body;

        if (!userId) {
            return res.json({ error: 'Missing userId' }, 400);
        }

        const result = await databases.listDocuments(
            databaseId,
            'users',
            [`equal("userId", [${userId}])`]
        );

        if (!result.documents.length) {
            return res.json({ error: 'User not found' }, 404);
        }

        return res.json({ success: true, user: result.documents[0] }, 200);
    } catch (err) {
        console.error('get_user_profile error:', err);
        return res.json({ error: 'Internal server error' }, 500);
    }
};
