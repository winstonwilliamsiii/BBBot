/**
 * /components/WatchlistTable.jsx
 * Display user's stock watchlist with add/remove functionality
 */

import { useState } from 'react';

export default function WatchlistTable({ items = [], onRemove = null, onRefresh = null }) {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const handleRemove = async (symbol) => {
    if (!confirm(`Remove ${symbol} from watchlist?`)) return;

    setLoading(true);
    setMessage(null);

    try {
      const response = await fetch('/api/removeFromWatchlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol })
      });

      const result = await response.json();

      if (response.ok) {
        setMessage({ type: 'success', text: `${symbol} removed from watchlist` });
        if (onRemove) onRemove(symbol);
        if (onRefresh) onRefresh();
      } else {
        setMessage({ type: 'error', text: result.error || 'Failed to remove symbol' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: error.message });
    } finally {
      setLoading(false);
    }
  };

  if (!items || items.length === 0) {
    return (
      <div className="watchlist-table">
        <h2>Watchlist</h2>
        <div className="empty-state">
          <p>No symbols in watchlist yet</p>
          <p className="hint">Add symbols from the dashboard</p>
        </div>
        <style jsx>{`
          .watchlist-table {
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 8px;
          }

          h2 {
            margin-top: 0;
            color: #333;
          }

          .empty-state {
            text-align: center;
            color: #666;
            padding: 40px 20px;
          }

          .hint {
            font-size: 13px;
            color: #999;
            margin: 10px 0 0 0;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="watchlist-table">
      <h2>Watchlist</h2>

      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Price</th>
              <th>Change</th>
              <th>% Change</th>
              <th>Notes</th>
              <th>Added</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr key={index}>
                <td className="symbol">{item.symbol}</td>
                <td className="price">${item.price?.toFixed(2) || 'N/A'}</td>
                <td className={`change ${item.change >= 0 ? 'positive' : 'negative'}`}>
                  {item.change >= 0 ? '+' : ''}{item.change?.toFixed(2) || 'N/A'}
                </td>
                <td className={`percent ${item.percent_change >= 0 ? 'positive' : 'negative'}`}>
                  {item.percent_change >= 0 ? '+' : ''}{item.percent_change?.toFixed(2) || 'N/A'}%
                </td>
                <td className="notes">{item.notes || '—'}</td>
                <td className="date">
                  {item.added_at ? new Date(item.added_at).toLocaleDateString() : '—'}
                </td>
                <td>
                  <button
                    onClick={() => handleRemove(item.symbol)}
                    disabled={loading}
                    className="remove-btn"
                    title="Remove from watchlist"
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <style jsx>{`
        .watchlist-table {
          padding: 20px;
          background-color: #f9f9f9;
          border-radius: 8px;
        }

        h2 {
          margin-top: 0;
          color: #333;
          margin-bottom: 20px;
        }

        .message {
          padding: 12px;
          border-radius: 4px;
          margin-bottom: 15px;
          font-size: 14px;
        }

        .message.success {
          background-color: #d4edda;
          color: #155724;
          border: 1px solid #c3e6cb;
        }

        .message.error {
          background-color: #f8d7da;
          color: #721c24;
          border: 1px solid #f5c6cb;
        }

        .table-container {
          overflow-x: auto;
        }

        table {
          width: 100%;
          border-collapse: collapse;
          background-color: white;
        }

        thead {
          background-color: #f0f0f0;
          border-bottom: 2px solid #ddd;
        }

        th {
          padding: 12px;
          text-align: left;
          font-weight: 600;
          color: #333;
          font-size: 13px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        td {
          padding: 12px;
          border-bottom: 1px solid #eee;
          font-size: 14px;
          color: #666;
        }

        tr:hover {
          background-color: #f5f5f5;
        }

        .symbol {
          font-weight: 600;
          color: #2c3e50;
        }

        .price {
          font-weight: 500;
          color: #333;
        }

        .change,
        .percent {
          font-weight: 500;
        }

        .change.positive,
        .percent.positive {
          color: #28a745;
        }

        .change.negative,
        .percent.negative {
          color: #dc3545;
        }

        .notes {
          font-size: 13px;
          color: #999;
          max-width: 150px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .date {
          font-size: 13px;
          color: #999;
        }

        .remove-btn {
          padding: 6px 12px;
          background-color: #dc3545;
          color: white;
          border: none;
          border-radius: 3px;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .remove-btn:hover:not(:disabled) {
          background-color: #c82333;
        }

        .remove-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}
