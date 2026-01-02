/**
 * /pages/api/recordBotMetrics.js
 * Secure API route for recording bot metrics and ML experiment results
 * Uses server-side API key for authentication with Appwrite
 */

import { createBotMetricsSecure, createAuditLogSecure } from '../../lib/serverAppwriteClient.js';

/**
 * Main API handler
 * POST /api/recordBotMetrics
 * 
 * Body:
 * {
 *   "user_id": "string",
 *   "bot_id": "string",
 *   "experiment_id": "string",
 *   "metrics": {
 *     "accuracy": 0.95,
 *     "sharpe_ratio": 1.23,
 *     "max_drawdown": -0.15,
 *     "total_return": 0.25,
 *     "win_rate": 0.62,
 *     "trades_executed": 45
 *   },
 *   "data_source": "yfinance|mysql|appwrite",
 *   "status": "completed|failed|in_progress",
 *   "notes": "string"
 * }
 */
export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Extract and validate request body
    const { user_id, bot_id, experiment_id, metrics, data_source, status = 'completed', notes } = req.body;

    // Input validation
    if (!user_id) {
      return res.status(400).json({ error: 'user_id is required' });
    }

    if (!bot_id) {
      return res.status(400).json({ error: 'bot_id is required' });
    }

    if (!metrics || typeof metrics !== 'object' || Object.keys(metrics).length === 0) {
      return res.status(400).json({ error: 'metrics object is required and cannot be empty' });
    }

    if (!['yfinance', 'mysql', 'appwrite'].includes(data_source)) {
      return res.status(400).json({ error: 'data_source must be one of: yfinance, mysql, appwrite' });
    }

    if (!['completed', 'failed', 'in_progress'].includes(status)) {
      return res.status(400).json({ error: 'status must be one of: completed, failed, in_progress' });
    }

    // Security: Get user IP and user agent for audit logging
    const userIp = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
    const userAgent = req.headers['user-agent'];

    // Call secure Appwrite function to create bot metrics
    const metricsResult = await createBotMetricsSecure({
      user_id,
      bot_id,
      experiment_id: experiment_id || `exp_${Date.now()}`,
      metrics,
      data_source,
      status,
      notes: notes || '',
      recorded_at: new Date().toISOString(),
      server_timestamp: new Date().toISOString()
    });

    // Log the metrics creation for audit trail
    await createAuditLogSecure({
      user_id,
      action: 'RECORD_BOT_METRICS',
      entity_type: 'bot_metric',
      entity_id: metricsResult?.id || 'unknown',
      changes: {
        bot_id,
        experiment_id,
        data_source,
        status,
        metrics_keys: Object.keys(metrics)
      },
      user_ip: userIp,
      user_agent: userAgent,
      timestamp: new Date().toISOString()
    }).catch(err => {
      // Log audit failure but don't fail the metrics creation
      console.error('Audit log creation failed:', err);
    });

    return res.status(200).json({
      success: true,
      data: metricsResult,
      message: 'Bot metrics recorded successfully'
    });

  } catch (error) {
    console.error('Bot metrics recording error:', error);
    
    return res.status(500).json({
      error: 'Failed to record bot metrics',
      message: error.message,
      // Don't expose internal error details in production
      ...(process.env.NODE_ENV === 'development' && { details: error.toString() })
    });
  }
}
