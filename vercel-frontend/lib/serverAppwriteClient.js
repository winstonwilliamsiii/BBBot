/**
 * Server-side Appwrite Client for Next.js API Routes
 * This module uses the APPWRITE_API_KEY (server-only, never exposed to client)
 * For secure communication with Appwrite Functions
 */

/**
 * Call an Appwrite Function from server-side with API key authentication
 * @param {string} functionId - The Appwrite Function ID
 * @param {object} payload - Data to send to the function
 * @returns {Promise<object>} - Function execution result
 */
export async function callAppwriteFunctionSecure(functionId, payload) {
  const endpoint = process.env.NEXT_PUBLIC_APPWRITE_ENDPOINT;
  const projectId = process.env.NEXT_PUBLIC_APPWRITE_PROJECT_ID;
  const apiKey = process.env.APPWRITE_API_KEY; // Server-side only!
  
  // Validate environment variables
  if (!endpoint || !projectId) {
    throw new Error('Missing Appwrite configuration. Check your .env.local file.');
  }

  if (!apiKey) {
    throw new Error('APPWRITE_API_KEY not configured for server-side requests');
  }

  try {
    const res = await fetch(`${endpoint}/functions/${functionId}/executions`, {
      method: 'POST',
      headers: {
        'X-Appwrite-Project': projectId,
        'X-Appwrite-Key': apiKey, // Server-only API key for authentication
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
    console.error('Secure Appwrite function call failed:', error);
    throw error;
  }
}

/**
 * Create a payment (server-side secure)
 * @param {object} paymentData - Payment details
 * @returns {Promise<object>} - Created payment
 */
export async function createPaymentSecure(paymentData) {
  const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_PAYMENT;
  
  if (!functionId) {
    throw new Error('NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_PAYMENT not set');
  }

  return callAppwriteFunctionSecure(functionId, paymentData);
}

/**
 * Create a transaction (server-side secure)
 * @param {object} transactionData - Transaction details
 * @returns {Promise<object>} - Created transaction
 */
export async function createTransactionSecure(transactionData) {
  const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_TRANSACTION;
  
  if (!functionId) {
    throw new Error('NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_TRANSACTION not set');
  }

  return callAppwriteFunctionSecure(functionId, transactionData);
}

/**
 * Create bot metrics (server-side secure)
 * @param {object} metricsData - Bot metrics data
 * @returns {Promise<object>} - Created metrics
 */
export async function createBotMetricsSecure(metricsData) {
  const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_BOT_METRIC;
  
  if (!functionId) {
    throw new Error('NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_BOT_METRIC not set');
  }

  return callAppwriteFunctionSecure(functionId, metricsData);
}

/**
 * Create audit log (server-side secure)
 * @param {object} auditData - Audit log details
 * @returns {Promise<object>} - Created audit log
 */
export async function createAuditLogSecure(auditData) {
  const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_AUDIT_LOG;
  
  if (!functionId) {
    throw new Error('NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CREATE_AUDIT_LOG not set');
  }

  return callAppwriteFunctionSecure(functionId, auditData);
}

/**
 * Get bot metrics (server-side secure)
 * @param {string} userId - User ID
 * @returns {Promise<object>} - Bot metrics
 */
export async function getBotMetricsSecure(userId) {
  const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_BOT_METRICS;
  
  if (!functionId) {
    throw new Error('NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_BOT_METRICS not set');
  }

  return callAppwriteFunctionSecure(functionId, {
    user_id: userId
  });
}

/**
 * Get bot metrics stats (server-side secure)
 * @param {string} userId - User ID
 * @returns {Promise<object>} - Bot metrics stats
 */
export async function getBotMetricsStatsSecure(userId) {
  const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_BOT_METRICS_STATS;
  
  if (!functionId) {
    throw new Error('NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_BOT_METRICS_STATS not set');
  }

  return callAppwriteFunctionSecure(functionId, {
    user_id: userId
  });
}
