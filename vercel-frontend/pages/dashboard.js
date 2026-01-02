/**
 * /pages/dashboard.js
 * Dashboard page - displays transactions and portfolio overview
 */

import { useEffect, useState } from 'react';

import DashboardTable from '../components/DashboardTable';

export default function Dashboard() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    totalTransactions: 0,
    totalBuys: 0,
    totalSells: 0,
    netValue: 0
  });

  useEffect(() => {
    fetchTransactions();
  }, []);

  const fetchTransactions = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/getTransactions');
      const data = await response.json();

      if (data.success) {
        setTransactions(data.transactions || []);
        calculateStats(data.transactions || []);
      } else {
        setError(data.error || 'Failed to fetch transactions');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (txns) => {
    const stats = {
      totalTransactions: txns.length,
      totalBuys: txns.filter(t => t.type === 'buy').length,
      totalSells: txns.filter(t => t.type === 'sell').length,
      netValue: txns.reduce((sum, t) => {
        const value = t.quantity * t.price;
        return sum + (t.type === 'buy' ? value : -value);
      }, 0)
    };
    setStats(stats);
  };

  const handleAddTransaction = async () => {
    // Open modal or navigate to payments
    const transactionData = {
      user_id: 'test_user',
      symbol: 'AAPL',
      type: 'buy',
      quantity: 10,
      price: 150.00,
      notes: 'New investment'
    };

    try {
      const response = await fetch('/api/createTransaction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(transactionData)
      });

      if (response.ok) {
        fetchTransactions(); // Refresh list
      }
    } catch (error) {
      console.error('Error creating transaction:', error);
    }
  };

  return (
    <div className="dashboard">
      <header className="page-header">
        <h1>Dashboard</h1>
        <p>Portfolio Overview & Transactions</p>
      </header>

      <main className="page-main">
        {/* Statistics Cards */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Total Transactions</div>
            <div className="stat-value">{stats.totalTransactions}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Buy Orders</div>
            <div className="stat-value" style={{ color: '#28a745' }}>
              {stats.totalBuys}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Sell Orders</div>
            <div className="stat-value" style={{ color: '#dc3545' }}>
              {stats.totalSells}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Net Value</div>
            <div className="stat-value" style={{ color: stats.netValue >= 0 ? '#28a745' : '#dc3545' }}>
              ${stats.netValue.toFixed(2)}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="actions">
          <button onClick={handleAddTransaction} className="btn btn-primary">
            + Add Transaction
          </button>
          <button onClick={fetchTransactions} disabled={loading} className="btn btn-secondary">
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Transactions Table */}
        {!loading && transactions.length > 0 ? (
          <DashboardTable transactions={transactions} />
        ) : !loading ? (
          <div className="empty-state">
            <p>No transactions yet</p>
            <p className="hint">Create your first transaction to get started</p>
          </div>
        ) : null}
      </main>

      <style jsx>{`
        .dashboard {
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

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 20px;
          margin-bottom: 30px;
        }

        .stat-card {
          background-color: white;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .stat-label {
          font-size: 13px;
          color: #999;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 10px;
        }

        .stat-value {
          font-size: 28px;
          font-weight: 700;
          color: #333;
        }

        .actions {
          display: flex;
          gap: 10px;
          margin-bottom: 30px;
          flex-wrap: wrap;
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
        }

        .btn-primary:hover {
          background-color: #5568d3;
        }

        .btn-secondary {
          background-color: #e9ecef;
          color: #333;
        }

        .btn-secondary:hover {
          background-color: #dee2e6;
        }

        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .error-message {
          background-color: #f8d7da;
          color: #721c24;
          padding: 15px;
          border-radius: 4px;
          border: 1px solid #f5c6cb;
          margin-bottom: 20px;
        }

        .empty-state {
          text-align: center;
          padding: 60px 20px;
          background-color: white;
          border-radius: 8px;
          color: #999;
        }

        .empty-state p {
          margin: 0;
          font-size: 18px;
        }

        .hint {
          font-size: 14px;
          margin-top: 8px !important;
        }

        @media (max-width: 768px) {
          .page-header h1 {
            font-size: 28px;
          }

          .stats-grid {
            grid-template-columns: repeat(2, 1fr);
          }

          .actions {
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
