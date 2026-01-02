/**
 * /pages/api/getMetrics.js
 * GET endpoint for retrieving bot metrics (wrapper around getBotMetrics)
 * Secure server-side call to Appwrite
 */

import { callAppwriteFunctionSecure } from '../../lib/serverAppwriteClient.js';

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { user_id, include_stats = false } = req.query;

    if (!user_id) {
      return res.status(400).json({ error: 'user_id is required' });
    }

    const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_BOT_METRICS;
    if (!functionId) {
      return res.status(500).json({ error: 'Function ID not configured' });
    }

    const metrics = await callAppwriteFunctionSecure(functionId, {
      user_id
    });

    let response = {
      success: true,
      data: metrics,
      timestamp: new Date().toISOString()
    };

    // Optionally include stats
    if (include_stats === 'true') {
      try {
        const statsFunctionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_BOT_METRICS_STATS;
        if (statsFunctionId) {
          const stats = await callAppwriteFunctionSecure(statsFunctionId, { user_id });
          response.stats = stats;
        }
      } catch (statsError) {
        console.warn('Stats retrieval failed (non-critical):', statsError);
      }
    }

    return res.status(200).json(response);

  } catch (error) {
    console.error('Get metrics error:', error);
    return res.status(500).json({
      error: 'Failed to retrieve metrics',
      message: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
}
