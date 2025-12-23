// #Appwrite_Client_Functions 

require('dotenv').config();
const sdk = require('node-appwrite');
const { ID } = require('node-appwrite');

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

// Initialize client with environment variables
const appwriteClient = createClient({
    endpoint: process.env.APPWRITE_ENDPOINT,
    projectId: process.env.APPWRITE_PROJECT_ID,
    apiKey: process.env.APPWRITE_API_KEY
});

const { databases } = appwriteClient;
const databaseId = process.env.APPWRITE_DATABASE_ID;

// Function 1: Create Transaction
async function create_transaction(userId, amount, description = '') {
    try {
        const now = new Date().toISOString();
        
        const response = await databases.createDocument(
            databaseId,
            'transactions',
            ID.unique(),
            {
                user_id: userId,
                amount: parseFloat(amount),
                description: description,
                date: now,
                created_at: now,
                updated_at: now
            }
        );
        
        console.log('✅ Transaction created:', response);
        return response;
    } catch (error) {
        console.error('❌ Error creating transaction:', error);
        throw error;
    }
}

// Function 2: Get Transactions
async function get_transactions(userId, limit = 100) {
    try {
        if (!userId) {
            throw new Error('Missing user_id');
        }

        const response = await databases.listDocuments(
            databaseId,
            'transactions',
            [
                `equal("user_id", ["${userId}"])`,
                `orderDesc("date")`,
                `limit(${limit})`
            ]
        );
        
        console.log(`✅ Retrieved ${response.documents.length} transactions for user ${userId}`);
        return response.documents;
    } catch (error) {
        console.error('❌ Error getting transactions:', error);
        throw error;
    }
}

// Function 3: Add to Watchlist
async function add_to_watchlist(userId, symbol) {
    try {
        if (!userId || !symbol) {
            throw new Error('Missing user_id or symbol');
        }

        const now = new Date().toISOString();
        
        const response = await databases.createDocument(
            databaseId,
            'watchlist',
            ID.unique(),
            {
                user_id: userId,
                symbol: symbol.toUpperCase(),
                added_at: now
            }
        );
        
        console.log(`✅ Added ${symbol} to watchlist for user ${userId}`);
        return response;
    } catch (error) {
        console.error('❌ Error adding to watchlist:', error);
        throw error;
    }
}

// Function 4: Get Watchlist
async function get_watchlist(userId) {
    try {
        if (!userId) {
            throw new Error('Missing user_id');
        }

        const response = await databases.listDocuments(
            databaseId,
            'watchlist',
            [
                `equal("user_id", ["${userId}"])`,
                `orderDesc("added_at")`
            ]
        );
        
        console.log(`✅ Retrieved watchlist for user ${userId}: ${response.documents.length} items`);
        return response.documents;
    } catch (error) {
        console.error('❌ Error getting watchlist:', error);
        throw error;
    }
}

// Function 5: Get User Profile
async function get_user_profile(userId) {
    try {
        if (!userId) {
            throw new Error('Missing user_id');
        }

        const response = await databases.listDocuments(
            databaseId,
            'users',
            [
                `equal("userId", [${parseInt(userId)}])`
            ]
        );
        
        if (response.documents.length === 0) {
            throw new Error(`User with ID ${userId} not found`);
        }
        
        const user = response.documents[0];
        // Remove sensitive data before returning
        delete user.password;
        
        console.log(`✅ Retrieved profile for user ${userId}`);
        return user;
    } catch (error) {
        console.error('❌ Error getting user profile:', error);
        throw error;
    }
}

// Function 6: Create Audit Log
async function create_audit_log(userId, action, actionDescription = '', ipAddress = '', userAgent = '') {
    try {
        if (!userId || !action) {
            throw new Error('Missing userId or action');
        }

        const now = new Date().toISOString();
        
        const response = await databases.createDocument(
            databaseId,
            'auditlogs',
            ID.unique(),
            {
                userId: parseInt(userId),
                action: action,
                actionDate: now,
                actionDescription: actionDescription,
                ipAddress: ipAddress,
                userAgent: userAgent
            }
        );
        
        console.log(`✅ Audit log created for user ${userId}: ${action}`);
        return response;
    } catch (error) {
        console.error('❌ Error creating audit log:', error);
        throw error;
    }
}

// Function 7: Get Audit Logs
async function get_audit_logs(userId, limit = 50) {
    try {
        if (!userId) {
            throw new Error('Missing user_id');
        }

        const response = await databases.listDocuments(
            databaseId,
            'auditlogs',
            [
                `equal("userId", [${parseInt(userId)}])`,
                `orderDesc("actionDate")`,
                `limit(${limit})`
            ]
        );
        
        console.log(`✅ Retrieved ${response.documents.length} audit logs for user ${userId}`);
        return response.documents;
    } catch (error) {
        console.error('❌ Error getting audit logs:', error);
        throw error;
    }
}

// Function 8: Create Payment
async function create_payment(userId, amount) {
    try {
        if (!userId || !amount) {
            throw new Error('Missing userId or amount');
        }

        const now = new Date().toISOString();
        
        const response = await databases.createDocument(
            databaseId,
            'payments',
            ID.unique(),
            {
                user_id: userId,
                amount: parseFloat(amount),
                created_at: now
            }
        );
        
        console.log(`✅ Payment created for user ${userId}: $${amount}`);
        return response;
    } catch (error) {
        console.error('❌ Error creating payment:', error);
        throw error;
    }
}

// Function 9: Get Payments
async function get_payments(userId, limit = 50) {
    try {
        if (!userId) {
            throw new Error('Missing user_id');
        }

        const response = await databases.listDocuments(
            databaseId,
            'payments',
            [
                `equal("user_id", ["${userId}"])`,
                `orderDesc("created_at")`,
                `limit(${limit})`
            ]
        );
        
        console.log(`✅ Retrieved ${response.documents.length} payments for user ${userId}`);
        return response.documents;
    } catch (error) {
        console.error('❌ Error getting payments:', error);
        throw error;
    }
}

// Function 10: Create Role
async function create_role(roleName) {
    try {
        if (!roleName) {
            throw new Error('Missing role_name');
        }

        const response = await databases.createDocument(
            databaseId,
            'roles',
            ID.unique(),
            {
                role_name: roleName.toLowerCase()
            }
        );
        
        console.log(`✅ Role created: ${roleName}`);
        return response;
    } catch (error) {
        console.error('❌ Error creating role:', error);
        throw error;
    }
}

// Function 11: Get Roles
async function get_roles() {
    try {
        const response = await databases.listDocuments(
            databaseId,
            'roles',
            [
                `orderAsc("role_name")`
            ]
        );
        
        console.log(`✅ Retrieved ${response.documents.length} roles`);
        return response.documents;
    } catch (error) {
        console.error('❌ Error getting roles:', error);
        throw error;
    }
}

// Function 12: Create Permission
async function create_permission(roleId, permission) {
    try {
        if (!roleId || !permission) {
            throw new Error('Missing role_id or permission');
        }

        const response = await databases.createDocument(
            databaseId,
            'permissions',
            ID.unique(),
            {
                role_id: roleId,
                permission: permission
            }
        );
        
        console.log(`✅ Permission created: ${permission} for role ${roleId}`);
        return response;
    } catch (error) {
        console.error('❌ Error creating permission:', error);
        throw error;
    }
}

// Function 13: Get Permissions
async function get_permissions(roleId) {
    try {
        if (!roleId) {
            throw new Error('Missing role_id');
        }

        const response = await databases.listDocuments(
            databaseId,
            'permissions',
            [
                `equal("role_id", ["${roleId}"])`,
                `orderAsc("permission")`
            ]
        );
        
        console.log(`✅ Retrieved ${response.documents.length} permissions for role ${roleId}`);
        return response.documents;
    } catch (error) {
        console.error('❌ Error getting permissions:', error);
        throw error;
    }
}

module.exports = { 
    createClient, 
    create_transaction, 
    get_transactions, 
    add_to_watchlist, 
    get_watchlist, 
    get_user_profile,
    create_audit_log,
    get_audit_logs,
    create_payment,
    get_payments,
    create_role,
    get_roles,
    create_permission,
    get_permissions
};