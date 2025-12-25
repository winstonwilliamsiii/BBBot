// Shared Appwrite Client for Serverless Functions
const sdk = require('node-appwrite');

function createClient({ endpoint, projectId, apiKey }) {
    const client = new sdk.Client()
        .setEndpoint(endpoint)
        .setProject(projectId)
        .setKey(apiKey);

    return {
        client,
        databases: new sdk.Databases(client),
        users: new sdk.Users(client)
    };
}

module.exports = { createClient };
