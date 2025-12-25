// BentleyBudgetBot Dashboard - Vercel Frontend

import { addToWatchlist, getTransactions, getWatchlist } from '../lib/appwriteClient';
import { useEffect, useState } from 'react';

export default function Dashboard() {
  const [transactions, setTransactions] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [newSymbol, setNewSymbol] = useState('');

  // Replace with actual user ID from your auth system
  const userId = 'user123';

  // Load initial data
  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    setLoading(true);
    setError(null);
    
    try {
      // Load transactions and watchlist in parallel
      const [txData, watchData] = await Promise.all([
        getTransactions(userId, 10),
        getWatchlist(userId)
      ]);
      
      setTransactions(txData.transactions || []);
      setWatchlist(watchData.watchlist || []);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAddToWatchlist(e) {
    e.preventDefault();
    if (!newSymbol.trim()) return;

    setLoading(true);
    setError(null);

    try {
      await addToWatchlist(userId, newSymbol.toUpperCase());
      setNewSymbol('');
      // Reload watchlist
      const watchData = await getWatchlist(userId);
      setWatchlist(watchData.watchlist || []);
    } catch (err) {
      console.error('Failed to add to watchlist:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>BentleyBudgetBot Dashboard</h1>

      {error && (
        <div style={{ 
          backgroundColor: '#fee', 
          padding: '10px', 
          borderRadius: '5px',
          marginBottom: '20px' 
        }}>
          ❌ Error: {error}
        </div>
      )}

      {/* Transactions Section */}
      <section style={{ marginBottom: '40px' }}>
        <h2>Recent Transactions</h2>
        <button 
          onClick={loadDashboardData}
          disabled={loading}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>

        {transactions.length === 0 ? (
          <p style={{ color: '#666', marginTop: '10px' }}>
            No transactions yet. Database is empty.
          </p>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {transactions.map((tx, index) => (
              <li 
                key={tx.$id || index}
                style={{
                  padding: '10px',
                  marginTop: '10px',
                  backgroundColor: '#f5f5f5',
                  borderRadius: '5px'
                }}
              >
                <strong>${tx.amount}</strong> on {tx.date}
                {tx.description && ` - ${tx.description}`}
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Watchlist Section */}
      <section>
        <h2>Stock Watchlist</h2>
        
        <form onSubmit={handleAddToWatchlist} style={{ marginBottom: '20px' }}>
          <input
            type="text"
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value)}
            placeholder="Enter stock symbol (e.g., AAPL)"
            style={{
              padding: '10px',
              marginRight: '10px',
              border: '1px solid #ccc',
              borderRadius: '5px',
              width: '200px'
            }}
          />
          <button
            type="submit"
            disabled={loading || !newSymbol.trim()}
            style={{
              padding: '10px 20px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            Add to Watchlist
          </button>
        </form>

        {watchlist.length === 0 ? (
          <p style={{ color: '#666' }}>
            No stocks in watchlist. Add some above!
          </p>
        ) : (
          <ul style={{ listStyle: 'none', padding: 0 }}>
            {watchlist.map((item, index) => (
              <li
                key={item.$id || index}
                style={{
                  padding: '10px',
                  marginTop: '10px',
                  backgroundColor: '#e8f5e9',
                  borderRadius: '5px'
                }}
              >
                <strong>{item.symbol}</strong>
                {item.notes && ` - ${item.notes}`}
                <span style={{ color: '#666', fontSize: '0.9em', marginLeft: '10px' }}>
                  Added: {new Date(item.added_date).toLocaleDateString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
