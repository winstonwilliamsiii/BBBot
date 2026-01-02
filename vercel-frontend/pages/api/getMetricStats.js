/**
 * /pages/api/getMetricStats.js
 * GET endpoint for retrieving aggregated bot metrics stats
 * Secure server-side call to Appwrite
 */

import { callAppwriteFunctionSecure } from '../../lib/serverAppwriteClient.js';

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { user_id } = req.query;

    if (!user_id) {
      return res.status(400).json({ error: 'user_id is required' });
    }

    const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_GET_BOT_METRICS_STATS;
    if (!functionId) {
      return res.status(500).json({ error: 'Function ID not configured' });
    }

    const stats = await callAppwriteFunctionSecure(functionId, {
      user_id
    });

    return res.status(200).json({
      success: true,
      data: stats,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Get metrics stats error:', error);
    return res.status(500).json({
      error: 'Failed to retrieve metrics stats',
      message: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
}
