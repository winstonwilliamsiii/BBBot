/**
 * /pages/api/getBotMetrics.js
 * Secure API route for retrieving bot metrics and ML experiment results
 * Uses server-side API key for authentication with Appwrite
 */

import { getBotMetricsSecure, getBotMetricsStatsSecure } from '../../lib/serverAppwriteClient.js';

/**
 * Main API handler
 * GET /api/getBotMetrics?user_id=string&include_stats=true
 */
export default async function handler(req, res) {
  // Only allow GET requests
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Extract query parameters
    const { user_id, include_stats } = req.query;

    // Input validation
    if (!user_id || typeof user_id !== 'string') {
      return res.status(400).json({ error: 'user_id query parameter is required' });
    }

    // Call secure Appwrite function to get bot metrics
    const metrics = await getBotMetricsSecure(user_id);

    let response = {
      success: true,
      data: metrics,
      timestamp: new Date().toISOString()
    };

    // Optionally include stats aggregation
    if (include_stats === 'true') {
      try {
        const stats = await getBotMetricsStatsSecure(user_id);
        response.stats = stats;
      } catch (statsError) {
        console.warn('Failed to retrieve metrics stats:', statsError);
        // Don't fail the request if stats are unavailable
      }
    }

    return res.status(200).json(response);

  } catch (error) {
    console.error('Get bot metrics error:', error);
    
    return res.status(500).json({
      error: 'Failed to retrieve bot metrics',
      message: error.message,
      // Don't expose internal error details in production
      ...(process.env.NODE_ENV === 'development' && { details: error.toString() })
    });
  }
}
