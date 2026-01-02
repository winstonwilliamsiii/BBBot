/**
 * /pages/api/createTransaction.js
 * Secure API route for creating transactions
 * Uses server-side API key for authentication with Appwrite
 */

import { createAuditLogSecure, createTransactionSecure } from '../../lib/serverAppwriteClient.js';

/**
 * Main API handler
 * POST /api/createTransaction
 * 
 * Body:
 * {
 *   "user_id": "string",
 *   "symbol": "AAPL",
 *   "quantity": number,
 *   "price": number,
 *   "type": "buy|sell",
 *   "transaction_date": "2026-01-01T00:00:00Z"
 * }
 */
export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Extract and validate request body
    const { user_id, symbol, quantity, price, type, transaction_date } = req.body;

    // Input validation
    if (!user_id) {
      return res.status(400).json({ error: 'user_id is required' });
    }

    if (!symbol || typeof symbol !== 'string' || symbol.length === 0) {
      return res.status(400).json({ error: 'symbol is required and must be a string' });
    }

    if (!quantity || quantity <= 0) {
      return res.status(400).json({ error: 'quantity must be a positive number' });
    }

    if (!price || price <= 0) {
      return res.status(400).json({ error: 'price must be a positive number' });
    }

    if (!type || !['buy', 'sell'].includes(type)) {
      return res.status(400).json({ error: 'type must be either "buy" or "sell"' });
    }

    // Security: Get user IP and user agent for audit logging
    const userIp = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
    const userAgent = req.headers['user-agent'];

    // Calculate transaction total
    const total = quantity * price;

    // Call secure Appwrite function to create transaction
    const transactionResult = await createTransactionSecure({
      user_id,
      symbol,
      quantity,
      price,
      total,
      type,
      transaction_date: transaction_date || new Date().toISOString(),
      created_at: new Date().toISOString()
    });

    // Log the transaction creation for audit trail
    await createAuditLogSecure({
      user_id,
      action: 'CREATE_TRANSACTION',
      entity_type: 'transaction',
      entity_id: transactionResult?.id || 'unknown',
      changes: {
        symbol,
        quantity,
        price,
        total,
        type
      },
      user_ip: userIp,
      user_agent: userAgent,
      timestamp: new Date().toISOString()
    }).catch(err => {
      // Log audit failure but don't fail the transaction creation
      console.error('Audit log creation failed:', err);
    });

    return res.status(200).json({
      success: true,
      data: transactionResult,
      message: 'Transaction created successfully'
    });

  } catch (error) {
    console.error('Transaction creation error:', error);
    
    return res.status(500).json({
      error: 'Failed to create transaction',
      message: error.message,
      // Don't expose internal error details in production
      ...(process.env.NODE_ENV === 'development' && { details: error.toString() })
    });
  }
}
