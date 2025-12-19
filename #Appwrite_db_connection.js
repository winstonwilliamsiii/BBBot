require('dotenv').config(); // Load environment variables
const sdk = require('node-appwrite');

/**
 * BENTLEY BUDGET BOT - APPWRITE DATABASE MANAGER
 * 
 * This script manages Appwrite database collections for BentleyBot.
 * 
 * COLLECTIONS OVERVIEW (8 total):
 * 
 * 1. team_members - Junction table (script-managed)
 *    - team_id: string(36) [required]
 *    - user_id: string(36) [required]
 * 
 * 2. transactions - Financial transactions (script-managed)
 *    - transaction_id: string(36) [required]
 *    - user_id: string(36) [required] 
 *    - amount: double [required]
 *    - date: datetime [required]
 *    - created_at: datetime [required]
 *    - updated_at: datetime [required]
 * 
 * 3. auditlogs - System audit trail (manually added)
 *    - auditId: integer [required]
 *    - userId: integer [required]
 *    - action: string(256) [required]
 *    - actionDate: datetime [required]
 *    - actionDescription: string(512) [optional]
 *    - ipAddress: string(45) [optional]
 *    - userAgent: string(256) [optional]
 * 
 * 4. users - User management (manually added)
 *    - username: string(64) [required]
 *    - password: string(255) [required]
 *    - email: email format [optional]
 *    - role: enum(user,admin,guest) [required]
 *    - userId: integer(1-max) [required]
 *    - status: enum(active,inactive,suspended) [optional]
 *    - firstName: string(64) [optional]
 * 
 * 5. watchlist - Investment watchlist (manually added) [empty - ready for attributes]
 * 6. permissions - User permissions (manually added) [empty - ready for attributes]  
 * 7. roles - Role definitions (manually added) [empty - ready for attributes]
 * 8. payments - Payment processing (manually added) [empty - ready for attributes]
 * 
 * Last Updated: 2025-12-19
 */

// Validate environment variables
const requiredEnvVars = ['APPWRITE_ENDPOINT', 'APPWRITE_PROJECT_ID', 'APPWRITE_API_KEY', 'APPWRITE_DATABASE_ID'];
requiredEnvVars.forEach((envVar) => {
    if (!process.env[envVar]) {
        console.error(`❌ Missing required environment variable: ${envVar}`);
        process.exit(1);
    }
});

// Init SDK using the correct Appwrite GitHub SDK pattern
const client = new sdk.Client()
    .setEndpoint(process.env.APPWRITE_ENDPOINT) // Your API Endpoint
    .setProject(process.env.APPWRITE_PROJECT_ID) // Your project ID
    .setKey(process.env.APPWRITE_API_KEY); // Your secret API key

const databases = new sdk.Databases(client);

// Function to list collections (from Appwrite GitHub SDK)
async function listCollections() {
    try {
        const result = await databases.listCollections({
            databaseId: process.env.APPWRITE_DATABASE_ID,
            queries: [], // optional
            total: false // optional
        });
        
        console.log('📋 Collections found:');
        console.log(JSON.stringify(result, null, 2));
        return result;
    } catch (error) {
        console.error('❌ Error listing collections:', error);
        throw error;
    }
}

// Create a collection for `team_members` junction table
async function createTeamMembersCollection() {
    try {
        const response = await databases.createCollection(
            process.env.APPWRITE_DATABASE_ID,
            'team_members',
            'Team Members',
            ['read("any")', 'write("any")'] // Simplified permissions as strings
        );

        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'team_members', 'team_id', 36, true);
        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'team_members', 'user_id', 36, true);

        console.log('✅ Team Members Collection Created:', response);
    } catch (error) {
        console.error('❌ Error Creating Team Members Collection:', error);
    }
}

// Create a collection for `transactions`
async function createTransactionsCollection() {
    try {
        const response = await databases.createCollection(
            process.env.APPWRITE_DATABASE_ID,
            'transactions',
            'Transactions',
            ['read("any")', 'write("any")'] // Simplified permissions as strings
        );

        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'transactions', 'transaction_id', 36, true);
        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'transactions', 'user_id', 36, true);
        await databases.createFloatAttribute(process.env.APPWRITE_DATABASE_ID, 'transactions', 'amount', true);
        await databases.createDatetimeAttribute(process.env.APPWRITE_DATABASE_ID, 'transactions', 'date', true);
        await databases.createDatetimeAttribute(process.env.APPWRITE_DATABASE_ID, 'transactions', 'created_at', true);
        await databases.createDatetimeAttribute(process.env.APPWRITE_DATABASE_ID, 'transactions', 'updated_at', true);

        console.log('✅ Transactions Collection Created:', response);
    } catch (error) {
        console.error('❌ Error Creating Transactions Collection:', error);
    }
}

// Execute the functions
async function main() {
    try {
        console.log('🚀 Starting Appwrite database operations...');
        
        // List existing collections
        const existingCollections = await listCollections();
        const existingIds = existingCollections.collections.map(col => col.$id);
        
        console.log('\n📊 Database Summary:');
        console.log(`Total Collections: ${existingCollections.total}`);
        console.log('Existing Collection IDs:', existingIds);
        
        // Only create collections that don't exist
        if (!existingIds.includes('team_members')) {
            console.log('\n🔨 Creating team_members collection...');
            await createTeamMembersCollection();
        } else {
            console.log('\n✅ team_members collection already exists');
        }
        
        if (!existingIds.includes('transactions')) {
            console.log('\n🔨 Creating transactions collection...');
            await createTransactionsCollection();
        } else {
            console.log('\n✅ transactions collection already exists');
        }
        
        console.log('\n🎉 Database operations completed successfully!');
        
    } catch (error) {
        console.error('❌ Main execution error:', error);
        process.exit(1);
    }
}

// Run the main function
main();