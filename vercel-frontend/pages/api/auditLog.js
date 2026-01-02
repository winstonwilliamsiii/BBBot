/**
 * /pages/api/auditLog.js
 * Secure API route for creating and retrieving audit logs
 * Uses server-side API key for authentication with Appwrite
 */

import { createAuditLogSecure } from '../../lib/serverAppwriteClient.js';

/**
 * Main API handler
 * POST /api/auditLog - Create audit log
 * GET /api/auditLog - Retrieve audit logs (future)
 */
export default async function handler(req, res) {
  if (req.method === 'POST') {
    return handlePostAuditLog(req, res);
  } else if (req.method === 'GET') {
    return handleGetAuditLogs(req, res);
  } else {
    return res.status(405).json({ error: 'Method not allowed' });
  }
}

/**
 * Handle POST - Create audit log
 * 
 * Body:
 * {
 *   "user_id": "string",
 *   "action": "CREATE_TRANSACTION|CREATE_PAYMENT|RECORD_BOT_METRICS|etc",
 *   "entity_type": "transaction|payment|bot_metric",
 *   "entity_id": "string",
 *   "changes": {},
 *   "details": "string" (optional)
 * }
 */
async function handlePostAuditLog(req, res) {
  try {
    const { user_id, action, entity_type, entity_id, changes, details } = req.body;

    // Input validation
    if (!user_id) {
      return res.status(400).json({ error: 'user_id is required' });
    }

    if (!action) {
      return res.status(400).json({ error: 'action is required' });
    }

    if (!entity_type) {
      return res.status(400).json({ error: 'entity_type is required' });
    }

    // Security: Get user IP and user agent
    const userIp = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
    const userAgent = req.headers['user-agent'];

    // Create audit log entry
    const auditResult = await createAuditLogSecure({
      user_id,
      action,
      entity_type,
      entity_id: entity_id || 'unknown',
      changes: changes || {},
      details: details || '',
      user_ip: userIp,
      user_agent: userAgent,
      timestamp: new Date().toISOString()
    });

    return res.status(201).json({
      success: true,
      data: auditResult,
      message: 'Audit log created successfully'
    });

  } catch (error) {
    console.error('Audit log creation error:', error);
    
    return res.status(500).json({
      error: 'Failed to create audit log',
      message: error.message,
      ...(process.env.NODE_ENV === 'development' && { details: error.toString() })
    });
  }
}

/**
 * Handle GET - Retrieve audit logs
 * Query params: user_id (required), limit (default 50)
 */
async function handleGetAuditLogs(req, res) {
  // This would call a GET_AUDIT_LOGS function
  // Placeholder for future implementation
  return res.status(200).json({
    message: 'Audit logs retrieval coming soon',
    note: 'Implement GET_AUDIT_LOGS function in Appwrite'
  });
}
