// Appwrite Client for Vercel/Next.js Frontend
// This calls Appwrite Functions via HTTP

/**
 * Call an Appwrite Function
 * @param {string} functionId - The Appwrite Function ID
 * @param {object} payload - Data to send to the function
 * @returns {Promise<object>} - Function execution result
 */
export async function callAppwriteFunction(functionId, payload) {
  const endpoint = process.env.NEXT_PUBLIC_APPWRITE_ENDPOINT;
  const projectId = process.env.NEXT_PUBLIC_APPWRITE_PROJECT_ID;
  
  // Validate environment variables
  if (!endpoint || !projectId) {
    throw new Error('Missing Appwrite configuration. Check your .env file.');
  }

  try {
    const res = await fetch(`${endpoint}/functions/${functionId}/executions`, {
      method: 'POST',
      headers: {
        'X-Appwrite-Project': projectId,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`Appwrite function error: ${res.status} ${res.statusText} - ${errorText}`);
    }

    const data = await res.json();
    
    // Appwrite returns execution data, response is in responseBody
    return data.responseBody ? JSON.parse(data.responseBody) : data;
    
  } catch (error) {
    console.error('Appwrite function call failed:', error);
    throw error;
  }
}

/**
 * Get user transactions
 * @param {string} userId - User ID
 * @param {number} limit - Max number of transactions
 * @returns {Promise<Array>} - Array of transactions
 */
export async function getTransactions(userId, limit = 10) {
  const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_TRANSACTIONS;
  
  if (!functionId) {
    throw new Error('NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_TRANSACTIONS not set');
  }

  return callAppwriteFunction(functionId, {
    user_id: userId,
    limit: limit
  });
}

/**
 * Get user watchlist
 * @param {string} userId - User ID
 * @returns {Promise<Array>} - Array of watchlist items
 */
export async function getWatchlist(userId) {
  const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_WATCHLIST;
  
  if (!functionId) {
    throw new Error('NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_WATCHLIST not set');
  }

  return callAppwriteFunction(functionId, {
    user_id: userId
  });
}

/**
 * Add stock to watchlist
 * @param {string} userId - User ID
 * @param {string} symbol - Stock symbol
 * @param {string} notes - Optional notes
 * @returns {Promise<object>} - Result of add operation
 */
export async function addToWatchlist(userId, symbol, notes = '') {
  const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_ADD_WATCHLIST;
  
  if (!functionId) {
    throw new Error('NEXT_PUBLIC_APPWRITE_FUNCTION_ID_ADD_WATCHLIST not set');
  }

  return callAppwriteFunction(functionId, {
    user_id: userId,
    symbol: symbol,
    notes: notes
  });
}

/**
 * Create a transaction
 * @param {object} transactionData - Transaction details
 * @returns {Promise<object>} - Created transaction
 */
export async function createTransaction(transactionData) {
  const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_TRANSACTION;
  
  if (!functionId) {
    throw new Error('NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_TRANSACTION not set');
  }

  return callAppwriteFunction(functionId, transactionData);
}

/**
 * Create a payment
 * @param {object} paymentData - Payment details
 * @returns {Promise<object>} - Created payment
 */
export async function createPayment(paymentData) {
  const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_PAYMENT;
  
  if (!functionId) {
    throw new Error('NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_PAYMENT not set');
  }

  return callAppwriteFunction(functionId, paymentData);
}

/**
 * Get bot metrics
 * @param {string} userId - User ID
 * @returns {Promise<object>} - Bot metrics
 */
export async function getBotMetrics(userId) {
  const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_BOT_METRICS;
  
  if (!functionId) {
    throw new Error('NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_BOT_METRICS not set');
  }

  return callAppwriteFunction(functionId, {
    user_id: userId
  });
}

/**
 * Create audit log
 * @param {object} auditData - Audit log details
 * @returns {Promise<object>} - Created audit log
 */
export async function createAuditLog(auditData) {
  const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_AUDIT_LOG;
  
  if (!functionId) {
    throw new Error('NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_AUDIT_LOG not set');
  }

  return callAppwriteFunction(functionId, auditData);
}

/**
 * Get user profile
 * @param {string} userId - User ID
 * @returns {Promise<object>} - User profile data
 */
export async function getUserProfile(userId) {
  const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_USER_PROFILE;
  
  if (!functionId) {
    throw new Error('NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_USER_PROFILE not set');
  }

  return callAppwriteFunction(functionId, {
    user_id: userId
  });
}
