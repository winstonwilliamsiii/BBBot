/**
 * /pages/watchlist.js
 * Watchlist page - manage stocks to track
 */

import { useEffect, useState } from 'react';

import WatchlistTable from '../components/WatchlistTable';

export default function Watchlist() {
  const [watchlistItems, setWatchlistItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newSymbol, setNewSymbol] = useState('');
  const [notes, setNotes] = useState('');
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const fetchWatchlist = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/addToWatchlist?get=true');
      const data = await response.json();

      if (data.success) {
        setWatchlistItems(data.watchlist || []);
      } else {
        // Initialize empty if no data
        setWatchlistItems([]);
      }
    } catch (err) {
      console.error('Error fetching watchlist:', err);
      setWatchlistItems([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSymbol = async (e) => {
    e.preventDefault();

    if (!newSymbol.trim()) {
      setError('Please enter a symbol');
      return;
    }

    setAdding(true);
    setError(null);

    try {
      const response = await fetch('/api/addToWatchlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: newSymbol.toUpperCase(),
          notes: notes.trim() || undefined
        })
      });

      const data = await response.json();

      if (response.ok) {
        setNewSymbol('');
        setNotes('');
        fetchWatchlist(); // Refresh list
      } else {
        setError(data.error || 'Failed to add symbol');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setAdding(false);
    }
  };

  const handleRemoveSymbol = (symbol) => {
    // WatchlistTable component handles removal
    // Just refresh the list after
    fetchWatchlist();
  };

  return (
    <div className="watchlist-page">
      <header className="page-header">
        <h1>Watchlist</h1>
        <p>Track and manage stocks you're monitoring</p>
      </header>

      <main className="page-main">
        {/* Add Symbol Form */}
        <div className="add-symbol-form">
          <h2>Add New Symbol</h2>
          
          {error && (
            <div className="error-message">
              <strong>Error:</strong> {error}
            </div>
          )}

          <form onSubmit={handleAddSymbol}>
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="symbol">Stock Symbol *</label>
                <input
                  id="symbol"
                  type="text"
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
                  placeholder="e.g., AAPL, GOOGL, MSFT"
                  maxLength="10"
                  disabled={adding}
                />
              </div>

              <div className="form-group">
                <label htmlFor="notes">Notes (optional)</label>
                <input
                  id="notes"
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g., Long-term investment"
                  disabled={adding}
                />
              </div>

              <button type="submit" className="btn btn-primary" disabled={adding || !newSymbol.trim()}>
                {adding ? 'Adding...' : '+ Add to Watchlist'}
              </button>
            </div>
          </form>
        </div>

        {/* Watchlist Display */}
        {loading ? (
          <div className="loading">
            <p>Loading watchlist...</p>
          </div>
        ) : (
          <WatchlistTable
            items={watchlistItems}
            onRemove={handleRemoveSymbol}
            onRefresh={fetchWatchlist}
          />
        )}
      </main>

      <style jsx>{`
        .watchlist-page {
          min-height: 100vh;
          background-color: #f5f7fa;
        }

        .page-header {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 40px 20px;
          text-align: center;
        }

        .page-header h1 {
          margin: 0 0 10px 0;
          font-size: 36px;
        }

        .page-header p {
          margin: 0;
          opacity: 0.9;
          font-size: 16px;
        }

        .page-main {
          max-width: 1200px;
          margin: 0 auto;
          padding: 30px 20px;
        }

        .add-symbol-form {
          background-color: white;
          border-radius: 8px;
          padding: 25px;
          margin-bottom: 30px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .add-symbol-form h2 {
          margin: 0 0 20px 0;
          color: #333;
          font-size: 20px;
        }

        .form-row {
          display: flex;
          gap: 15px;
          flex-wrap: wrap;
          align-items: flex-end;
        }

        .form-group {
          flex: 1;
          min-width: 200px;
        }

        .form-group label {
          display: block;
          margin-bottom: 8px;
          font-weight: 600;
          color: #333;
          font-size: 14px;
        }

        .form-group input {
          width: 100%;
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
          font-family: inherit;
        }

        .form-group input:focus {
          outline: none;
          border-color: #667eea;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .form-group input:disabled {
          background-color: #f5f5f5;
          cursor: not-allowed;
        }

        .btn {
          padding: 10px 20px;
          border: none;
          border-radius: 4px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-primary {
          background-color: #667eea;
          color: white;
          white-space: nowrap;
        }

        .btn-primary:hover:not(:disabled) {
          background-color: #5568d3;
        }

        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .error-message {
          background-color: #f8d7da;
          color: #721c24;
          padding: 12px;
          border-radius: 4px;
          border: 1px solid #f5c6cb;
          margin-bottom: 15px;
          font-size: 14px;
        }

        .loading {
          text-align: center;
          padding: 60px 20px;
          background-color: white;
          border-radius: 8px;
          color: #999;
        }

        @media (max-width: 768px) {
          .page-header h1 {
            font-size: 28px;
          }

          .form-row {
            flex-direction: column;
          }

          .btn {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
}
