/**
 * /pages/api/createPayment.js
 * Secure API route for creating payments
 * Uses server-side API key for authentication with Appwrite
 */

import { createPaymentSecure, createAuditLogSecure } from '../../lib/serverAppwriteClient.js';

/**
 * Main API handler
 * POST /api/createPayment
 * 
 * Body:
 * {
 *   "user_id": "string",
 *   "amount": number,
 *   "currency": "USD",
 *   "description": "string",
 *   "payment_method": "credit_card|debit_card|bank_transfer"
 * }
 */
export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Extract and validate request body
    const { user_id, amount, currency = 'USD', description, payment_method } = req.body;

    // Input validation
    if (!user_id) {
      return res.status(400).json({ error: 'user_id is required' });
    }

    if (!amount || amount <= 0) {
      return res.status(400).json({ error: 'amount must be a positive number' });
    }

    if (!payment_method) {
      return res.status(400).json({ error: 'payment_method is required' });
    }

    // Security: Get user IP and user agent for audit logging
    const userIp = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
    const userAgent = req.headers['user-agent'];

    // Call secure Appwrite function to create payment
    const paymentResult = await createPaymentSecure({
      user_id,
      amount,
      currency,
      description,
      payment_method,
      created_at: new Date().toISOString()
    });

    // Log the payment creation for audit trail
    await createAuditLogSecure({
      user_id,
      action: 'CREATE_PAYMENT',
      entity_type: 'payment',
      entity_id: paymentResult?.id || 'unknown',
      changes: {
        amount,
        currency,
        payment_method
      },
      user_ip: userIp,
      user_agent: userAgent,
      timestamp: new Date().toISOString()
    }).catch(err => {
      // Log audit failure but don't fail the payment creation
      console.error('Audit log creation failed:', err);
    });

    return res.status(200).json({
      success: true,
      data: paymentResult,
      message: 'Payment created successfully'
    });

  } catch (error) {
    console.error('Payment creation error:', error);
    
    return res.status(500).json({
      error: 'Failed to create payment',
      message: error.message,
      // Don't expose internal error details in production
      ...(process.env.NODE_ENV === 'development' && { details: error.toString() })
    });
  }
}
