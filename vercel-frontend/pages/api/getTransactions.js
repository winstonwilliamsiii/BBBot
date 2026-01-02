/**
 * /pages/api/getTransactions.js
 * GET endpoint for retrieving user transactions
 * Secure server-side call to Appwrite
 */

import { callAppwriteFunctionSecure } from '../../lib/serverAppwriteClient.js';

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { user_id, limit = 50 } = req.query;

    if (!user_id) {
      return res.status(400).json({ error: 'user_id is required' });
    }

    const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_TRANSACTIONS;
    if (!functionId) {
      return res.status(500).json({ error: 'Function ID not configured' });
    }

    const transactions = await callAppwriteFunctionSecure(functionId, {
      user_id,
      limit: parseInt(limit)
    });

    return res.status(200).json({
      success: true,
      data: transactions,
      count: Array.isArray(transactions) ? transactions.length : 0
    });

  } catch (error) {
    console.error('Get transactions error:', error);
    return res.status(500).json({
      error: 'Failed to retrieve transactions',
      message: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
}
