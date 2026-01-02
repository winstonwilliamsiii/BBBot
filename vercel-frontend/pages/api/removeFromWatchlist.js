/**
 * /pages/api/removeFromWatchlist.js
 * POST endpoint for removing stocks from watchlist
 * Secure server-side call to Appwrite
 */

import { callAppwriteFunctionSecure } from '../../lib/serverAppwriteClient.js';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { user_id, symbol } = req.body;

    if (!user_id) {
      return res.status(400).json({ error: 'user_id is required' });
    }

    if (!symbol || typeof symbol !== 'string') {
      return res.status(400).json({ error: 'symbol is required' });
    }

    // Note: This assumes you have a REMOVE_WATCHLIST function in Appwrite
    // If not, adjust the function ID
    const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_REMOVE_WATCHLIST;
    if (!functionId) {
      return res.status(500).json({ error: 'Remove watchlist function not configured' });
    }

    const result = await callAppwriteFunctionSecure(functionId, {
      user_id,
      symbol: symbol.toUpperCase()
    });

    return res.status(200).json({
      success: true,
      data: result,
      message: `${symbol} removed from watchlist`
    });

  } catch (error) {
    console.error('Remove from watchlist error:', error);
    return res.status(500).json({
      error: 'Failed to remove from watchlist',
      message: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
}
