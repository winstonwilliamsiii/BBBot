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

// RBAC Authorization Helper Functions
async function getUserRole(userId) {
    try {
        const response = await databases.listDocuments(
            databaseId,
            'users',
            [`equal("userId", [${parseInt(userId)}])`]
        );
        
        if (response.documents.length === 0) {
            throw new Error('User not found');
        }
        
        return response.documents[0].role;
    } catch (error) {
        console.error('❌ Error getting user role:', error);
        throw error;
    }
}

async function checkPermission(userId, requiredPermission) {
    try {
        const userRole = await getUserRole(userId);
        
        // Get role ID first
        const roleResponse = await databases.listDocuments(
            databaseId,
            'roles',
            [`equal("role_name", ["${userRole}"])`]
        );
        
        if (roleResponse.documents.length === 0) {
            throw new Error('Role not found');
        }
        
        const roleId = roleResponse.documents[0].$id;
        
        // Check permissions for this role
        const permResponse = await databases.listDocuments(
            databaseId,
            'permissions',
            [
                `equal("role_id", ["${roleId}"])`,
                `equal("permission", ["${requiredPermission}"])`
            ]
        );
        
        return permResponse.documents.length > 0;
    } catch (error) {
        console.error('❌ Error checking permission:', error);
        return false;
    }
}

async function authorize(userId, action, resourceId = null) {
    try {
        const userRole = await getUserRole(userId);
        
        // Admin can do everything
        if (userRole === 'admin') {
            return true;
        }
        
        // Check specific permissions
        const hasPermission = await checkPermission(userId, action);
        
        // For user role, they can only access their own resources
        if (userRole === 'user' && resourceId && resourceId !== userId) {
            return false;
        }
        
        return hasPermission;
    } catch (error) {
        console.error('❌ Authorization error:', error);
        return false;
    }
}

// Function 1: Create Transaction (with RBAC)
async function create_transaction(requesterId, userId, amount, description = '') {
    try {
        // Authorization check
        const isAuthorized = await authorize(requesterId, 'create_transaction', userId);
        if (!isAuthorized) {
            throw new Error('Unauthorized: Insufficient permissions to create transaction');
        }

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
        
        // Create audit log
        await create_audit_log(requesterId, 'CREATE_TRANSACTION', `Created transaction for user ${userId}: $${amount}`);
        
        console.log('✅ Transaction created:', response);
        return response;
    } catch (error) {
        console.error('❌ Error creating transaction:', error);
        throw error;
    }
}

// Function 2: Get Transactions (with RBAC)
async function get_transactions(requesterId, userId, limit = 100) {
    try {
        if (!userId) {
            throw new Error('Missing user_id');
        }

        // Authorization check
        const isAuthorized = await authorize(requesterId, 'read_transactions', userId);
        if (!isAuthorized) {
            throw new Error('Unauthorized: Insufficient permissions to read transactions');
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

// Function 3: Add to Watchlist (with RBAC)
async function add_to_watchlist(requesterId, userId, symbol) {
    try {
        if (!userId || !symbol) {
            throw new Error('Missing user_id or symbol');
        }

        // Authorization check
        const isAuthorized = await authorize(requesterId, 'create_watchlist', userId);
        if (!isAuthorized) {
            throw new Error('Unauthorized: Insufficient permissions to modify watchlist');
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
        
        // Create audit log
        await create_audit_log(requesterId, 'ADD_WATCHLIST', `Added ${symbol} to watchlist for user ${userId}`);
        
        console.log(`✅ Added ${symbol} to watchlist for user ${userId}`);
        return response;
    } catch (error) {
        console.error('❌ Error adding to watchlist:', error);
        throw error;
    }
}

// Function 4: Get Watchlist (with RBAC)
async function get_watchlist(requesterId, userId) {
    try {
        if (!userId) {
            throw new Error('Missing user_id');
        }

        // Authorization check
        const isAuthorized = await authorize(requesterId, 'read_watchlist', userId);
        if (!isAuthorized) {
            throw new Error('Unauthorized: Insufficient permissions to read watchlist');
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

// Function 5: Get User Profile (with RBAC)
async function get_user_profile(requesterId, userId) {
    try {
        if (!userId) {
            throw new Error('Missing user_id');
        }

        // Authorization check
        const isAuthorized = await authorize(requesterId, 'read_profile', userId);
        if (!isAuthorized) {
            throw new Error('Unauthorized: Insufficient permissions to read profile');
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
    // RBAC Helper Functions
    getUserRole,
    checkPermission,
    authorize,
    // Core RBAC-Protected Functions
    create_transaction, 
    get_transactions, 
    add_to_watchlist, 
    get_watchlist, 
    get_user_profile,
    // Audit & Admin Functions
    create_audit_log,
    get_audit_logs,
    create_payment,
    get_payments,
    create_role,
    get_roles,
    create_permission,
    get_permissions
};

// ===== SERVERLESS FUNCTION TEMPLATES =====
// These are template functions for Appwrite Function deployment

/**
 * Serverless Create Transaction Function Template
 * Deploy this as a separate Appwrite Function
 * 
 * Usage: Copy this function to a new file for Appwrite Function deployment
 */
const serverless_create_transaction = `
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
                [\`equal("userId", [\${parseInt(requester_id)}])\`]
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
                actionDescription: \`Created transaction for user \${user_id}: $\${amount}\`,
                ipAddress: req.headers['x-forwarded-for'] || req.headers['remote-addr'] || '',
                userAgent: req.headers['user-agent'] || ''
            }
        );

        return res.json({ 
            success: true, 
            transaction: tx,
            message: \`Transaction created successfully for user \${user_id}\`
        }, 201);
    } catch (err) {
        console.error('create_transaction error:', err);
        return res.json({ error: 'Internal server error', details: err.message }, 500);
    }
};
`;

/**
 * Serverless Get Transactions Function Template
 * Deploy this as a separate Appwrite Function
 */
const serverless_get_transactions = `
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
        const { requester_id, user_id, limit = 100 } = body;

        if (!requester_id || !user_id) {
            return res.json({ error: 'Missing required fields: requester_id, user_id' }, 400);
        }

        // RBAC Authorization Check
        try {
            const userResponse = await databases.listDocuments(
                databaseId,
                'users',
                [\`equal("userId", [\${parseInt(requester_id)}])\`]
            );
            
            if (userResponse.documents.length === 0) {
                return res.json({ error: 'Requester not found' }, 404);
            }
            
            const requesterRole = userResponse.documents[0].role;
            
            if (requesterRole !== 'admin' && requester_id !== user_id) {
                return res.json({ error: 'Unauthorized: Insufficient permissions' }, 403);
            }
        } catch (authError) {
            return res.json({ error: 'Authorization failed' }, 403);
        }

        const result = await databases.listDocuments(
            databaseId,
            'transactions',
            [
                \`equal("user_id", ["\${user_id}"])\`,
                \`orderDesc("date")\`,
                \`limit(\${limit})\`
            ]
        );

        return res.json({ 
            success: true, 
            transactions: result.documents,
            total: result.documents.length,
            message: \`Retrieved \${result.documents.length} transactions for user \${user_id}\`
        }, 200);
    } catch (err) {
        console.error('get_transactions error:', err);
        return res.json({ error: 'Internal server error', details: err.message }, 500);
    }
};
`;

/**
 * Serverless Get Transactions for StreamLit Function Template
 * Simplified version for StreamLit integration without RBAC
 * Deploy this as a separate Appwrite Function
 */
const serverless_get_transactions_streamlit = `
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
        const { user_id, limit = 100 } = body;

        if (!user_id) {
            return res.json({ error: 'Missing user_id' }, 400);
        }

        const result = await databases.listDocuments(
            databaseId,
            'transactions',
            [
                \`equal("user_id", ["\${user_id}"])\`,
                \`orderDesc("date")\`,
                \`limit(\${limit})\`
            ]
        );

        return res.json({ success: true, transactions: result.documents }, 200);
    } catch (err) {
        console.error('get_transactions error:', err);
        return res.json({ error: 'Internal server error' }, 500);
    }
};
`;

// Export serverless templates for reference
module.exports.serverless_templates = {
    create_transaction: serverless_create_transaction,
    get_transactions: serverless_get_transactions,
    get_transactions_streamlit: serverless_get_transactions_streamlit
};