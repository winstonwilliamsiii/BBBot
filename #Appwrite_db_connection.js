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
const functions = new sdk.Functions(client);

/**
 * APPWRITE FUNCTIONS EXECUTION
 * 
 * Execute Appwrite Functions with data payload
 * Python equivalent (for reference):
 * 
 * import requests
 * response = requests.post(
 *     "https://cloud.appwrite.io/v1/functions/<functionId>/executions",
 *     headers={"X-Appwrite-Key": APPWRITE_API_KEY},
 *     json={"symbol": "AAPL", "quantity": 5}
 * )
 */

// Execute an Appwrite Function
async function executeFunction(functionId, data = {}) {
    try {
        const execution = await functions.createExecution(
            functionId,
            JSON.stringify(data), // body
            false, // async
            '/', // path
            'POST', // method
            {} // headers
        );
        
        console.log('🚀 Function executed successfully:');
        console.log(`Function ID: ${functionId}`);
        console.log(`Execution ID: ${execution.$id}`);
        console.log(`Status: ${execution.status}`);
        console.log('Response:', execution.responseBody);
        
        return execution;
    } catch (error) {
        console.error('❌ Error executing function:', error);
        throw error;
    }
}

// Example function to execute stock trading function
async function executeStockTrade(symbol, quantity) {
    const functionId = 'YOUR_FUNCTION_ID'; // Replace with your actual function ID
    const data = {
        symbol: symbol,
        quantity: quantity
    };
    
    try {
        const result = await executeFunction(functionId, data);
        return result;
    } catch (error) {
        console.error(`❌ Failed to execute stock trade for ${symbol}:`, error);
        throw error;
    }
}

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

        // Create index for efficient user/date queries
        await databases.createIndex(
            process.env.APPWRITE_DATABASE_ID,
            'transactions',
            'idx_user_date',
            'key',
            ['user_id', 'date'],
            ['ASC', 'DESC']
        );

        console.log('✅ Transactions Collection Created:', response);
    } catch (error) {
        console.error('❌ Error Creating Transactions Collection:', error);
    }
}

// Create a collection for `auditlogs` system audit trail
async function createAuditLogsCollection() {
    try {
        const response = await databases.createCollection(
            process.env.APPWRITE_DATABASE_ID,
            'auditlogs',
            'Audit Logs',
            ['read("any")', 'write("any")']
        );

        await databases.createIntegerAttribute(process.env.APPWRITE_DATABASE_ID, 'auditlogs', 'auditId', true);
        await databases.createIntegerAttribute(process.env.APPWRITE_DATABASE_ID, 'auditlogs', 'userId', true);
        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'auditlogs', 'action', 256, true);
        await databases.createDatetimeAttribute(process.env.APPWRITE_DATABASE_ID, 'auditlogs', 'actionDate', true);
        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'auditlogs', 'actionDescription', 512, false);
        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'auditlogs', 'ipAddress', 45, false);
        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'auditlogs', 'userAgent', 256, false);

        console.log('✅ Audit Logs Collection Created:', response);
    } catch (error) {
        console.error('❌ Error Creating Audit Logs Collection:', error);
    }
}

// Create a collection for `users` user management
async function createUsersCollection() {
    try {
        const response = await databases.createCollection(
            process.env.APPWRITE_DATABASE_ID,
            'users',
            'Users',
            ['read("any")', 'write("any")']
        );

        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'users', 'username', 64, true);
        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'users', 'password', 255, true);
        await databases.createEmailAttribute(process.env.APPWRITE_DATABASE_ID, 'users', 'email', false);
        await databases.createEnumAttribute(process.env.APPWRITE_DATABASE_ID, 'users', 'role', ['user', 'admin', 'guest'], true);
        await databases.createIntegerAttribute(process.env.APPWRITE_DATABASE_ID, 'users', 'userId', true, 1);
        await databases.createEnumAttribute(process.env.APPWRITE_DATABASE_ID, 'users', 'status', ['active', 'inactive', 'suspended'], false);
        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'users', 'firstName', 64, false);

        console.log('✅ Users Collection Created:', response);
    } catch (error) {
        console.error('❌ Error Creating Users Collection:', error);
    }
}

// Create a collection for `watchlist` investment watchlist
async function createWatchlistCollection() {
    try {
        const response = await databases.createCollection(
            process.env.APPWRITE_DATABASE_ID,
            'watchlist',
            'Watchlist',
            ['read("any")', 'write("any")']
        );

        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'watchlist', 'user_id', 36, true);
        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'watchlist', 'symbol', 16, true);
        await databases.createDatetimeAttribute(process.env.APPWRITE_DATABASE_ID, 'watchlist', 'added_at', true);

        console.log('✅ Watchlist Collection Created:', response);
    } catch (error) {
        console.error('❌ Error Creating Watchlist Collection:', error);
    }
}

// Create a collection for `permissions` user permissions
async function createPermissionsCollection() {
    try {
        const response = await databases.createCollection(
            process.env.APPWRITE_DATABASE_ID,
            'permissions',
            'Permissions',
            ['read("any")', 'write("any")']
        );

        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'permissions', 'role_id', 36, true);
        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'permissions', 'permission', 128, true);

        console.log('✅ Permissions Collection Created:', response);
    } catch (error) {
        console.error('❌ Error Creating Permissions Collection:', error);
    }
}

// Create a collection for `roles` role definitions
async function createRolesCollection() {
    try {
        const response = await databases.createCollection(
            process.env.APPWRITE_DATABASE_ID,
            'roles',
            'Roles',
            ['read("any")', 'write("any")']
        );

        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'roles', 'role_id', 36, true);
        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'roles', 'role_name', 64, true);

        console.log('✅ Roles Collection Created:', response);
    } catch (error) {
        console.error('❌ Error Creating Roles Collection:', error);
    }
}

// Create a collection for `payments` payment processing
async function createPaymentsCollection() {
    try {
        const response = await databases.createCollection(
            process.env.APPWRITE_DATABASE_ID,
            'payments',
            'Payments',
            ['read("any")', 'write("any")']
        );

        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'payments', 'payment_id', 36, true);
        await databases.createStringAttribute(process.env.APPWRITE_DATABASE_ID, 'payments', 'user_id', 36, true);
        await databases.createFloatAttribute(process.env.APPWRITE_DATABASE_ID, 'payments', 'amount', true);
        await databases.createDatetimeAttribute(process.env.APPWRITE_DATABASE_ID, 'payments', 'created_at', true);

        console.log('✅ Payments Collection Created:', response);
    } catch (error) {
        console.error('❌ Error Creating Payments Collection:', error);
    }
}

// Execute the functions
async function main() {
    try {
        console.log('🚀 Starting Appwrite database provisioning...');
        
        // List existing collections
        const existingCollections = await listCollections();
        const existingIds = existingCollections.collections.map(col => col.$id);
        
        console.log('\n📊 Database Summary:');
        console.log(`Total Collections: ${existingCollections.total}`);
        console.log('Existing Collection IDs:', existingIds);
        
        // Only create collections that don't exist
        const tasks = [
            { id: 'team_members', fn: createTeamMembersCollection },
            { id: 'transactions', fn: createTransactionsCollection },
            { id: 'auditlogs', fn: createAuditLogsCollection },
            { id: 'users', fn: createUsersCollection },
            { id: 'watchlist', fn: createWatchlistCollection },
            { id: 'permissions', fn: createPermissionsCollection },
            { id: 'roles', fn: createRolesCollection },
            { id: 'payments', fn: createPaymentsCollection }
        ];

        for (const task of tasks) {
            if (!existingIds.includes(task.id)) {
                console.log(`\n🔨 Creating ${task.id} collection...`);
                await task.fn();
            } else {
                console.log(`\n✅ ${task.id} collection already exists`);
            }
        }
        
        // Example: Execute a function (uncomment and configure as needed)
        // console.log('\n🔧 Testing function execution...');
        // await executeStockTrade('AAPL', 5);
        
        console.log('\n🎉 All collections provisioned successfully!');
        
    } catch (error) {
        console.error('❌ Provisioning error:', error);
        process.exit(1);
    }
}

// Run the main function
main();