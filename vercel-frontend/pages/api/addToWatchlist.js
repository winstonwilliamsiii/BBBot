/**
 * /pages/api/addToWatchlist.js
 * POST endpoint for adding stocks to watchlist
 * Secure server-side call to Appwrite
 */

import { callAppwriteFunctionSecure } from '../../lib/serverAppwriteClient.js';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { user_id, symbol, notes = '' } = req.body;

    if (!user_id) {
      return res.status(400).json({ error: 'user_id is required' });
    }

    if (!symbol || typeof symbol !== 'string' || symbol.length === 0) {
      return res.status(400).json({ error: 'symbol is required and must be a string' });
    }

    const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_ADD_WATCHLIST;
    if (!functionId) {
      return res.status(500).json({ error: 'Function ID not configured' });
    }

    const result = await callAppwriteFunctionSecure(functionId, {
      user_id,
      symbol: symbol.toUpperCase(),
      notes,
      added_at: new Date().toISOString()
    });

    return res.status(201).json({
      success: true,
      data: result,
      message: `${symbol} added to watchlist`
    });

  } catch (error) {
    console.error('Add to watchlist error:', error);
    return res.status(500).json({
      error: 'Failed to add to watchlist',
      message: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
}
