/**
 * /pages/metrics.js
 * ML Metrics page - view bot performance and experiment results
 */

import { useEffect, useState } from 'react';

import MetricsChart from '../components/MetricsChart';

export default function Metrics() {
  const [metrics, setMetrics] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBot, setSelectedBot] = useState(null);

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch metrics
      const response = await fetch('/api/getMetrics');
      const data = await response.json();

      if (data.success) {
        setMetrics(data.metrics || []);
        
        // Fetch stats
        try {
          const statsResponse = await fetch('/api/getMetricStats');
          const statsData = await statsResponse.json();
          if (statsData.success) {
            setStats(statsData.stats);
          }
        } catch (err) {
          console.warn('Could not fetch stats:', err);
        }
      } else {
        setError(data.error || 'Failed to fetch metrics');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBotSelect = (botId) => {
    setSelectedBot(selectedBot === botId ? null : botId);
  };

  // Group metrics by bot_id
  const groupedMetrics = metrics.reduce((acc, metric) => {
    const botId = metric.bot_id || 'unknown';
    if (!acc[botId]) {
      acc[botId] = [];
    }
    acc[botId].push(metric);
    return acc;
  }, {});

  return (
    <div className="metrics-page">
      <header className="page-header">
        <h1>ML Metrics</h1>
        <p>Monitor bot performance and ML experiment results</p>
      </header>

      <main className="page-main">
        {/* Overall Statistics */}
        {stats && (
          <div className="stats-overview">
            <h2>Overall Performance</h2>
            <div className="stats-cards">
              <div className="stat-card">
                <div className="stat-label">Total Experiments</div>
                <div className="stat-value">{stats.total_experiments || 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Avg Accuracy</div>
                <div className="stat-value">
                  {stats.avg_accuracy ? `${(stats.avg_accuracy * 100).toFixed(2)}%` : 'N/A'}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Active Bots</div>
                <div className="stat-value">{stats.active_bots || 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Avg Return</div>
                <div className="stat-value">
                  {stats.avg_return ? `${(stats.avg_return * 100).toFixed(2)}%` : 'N/A'}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="actions">
          <button onClick={fetchMetrics} disabled={loading} className="btn btn-primary">
            {loading ? 'Loading...' : 'Refresh Metrics'}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Metrics by Bot */}
        {!loading && Object.keys(groupedMetrics).length > 0 ? (
          <div className="metrics-by-bot">
            {Object.entries(groupedMetrics).map(([botId, botMetrics]) => (
              <div key={botId} className="bot-section">
                <div
                  className="bot-header"
                  onClick={() => handleBotSelect(botId)}
                >
                  <h3>{botId || 'Unknown Bot'}</h3>
                  <span className="metric-count">{botMetrics.length} metrics</span>
                  <span className={`toggle ${selectedBot === botId ? 'open' : ''}`}>▼</span>
                </div>

                {selectedBot === botId && (
                  <div className="bot-metrics">
                    {botMetrics.map((metric, index) => (
                      <MetricsChart key={index} metric={metric} />
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : !loading ? (
          <div className="empty-state">
            <p>No metrics recorded yet</p>
            <p className="hint">Metrics will appear here after your bots run experiments</p>
          </div>
        ) : null}
      </main>

      <style jsx>{`
        .metrics-page {
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

        .stats-overview {
          margin-bottom: 40px;
        }

        .stats-overview h2 {
          margin: 0 0 20px 0;
          color: #333;
          font-size: 20px;
        }

        .stats-cards {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 20px;
        }

        .stat-card {
          background-color: white;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          text-align: center;
        }

        .stat-label {
          font-size: 12px;
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
          padding: 15px;
          border-radius: 4px;
          border: 1px solid #f5c6cb;
          margin-bottom: 20px;
        }

        .metrics-by-bot {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .bot-section {
          background-color: white;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .bot-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px;
          background-color: #f9f9f9;
          border-bottom: 1px solid #eee;
          cursor: pointer;
          user-select: none;
          transition: background-color 0.2s;
        }

        .bot-header:hover {
          background-color: #f5f5f5;
        }

        .bot-header h3 {
          margin: 0;
          color: #333;
          font-size: 16px;
        }

        .metric-count {
          font-size: 13px;
          color: #999;
          background-color: #e9ecef;
          padding: 4px 8px;
          border-radius: 3px;
        }

        .toggle {
          color: #999;
          transition: transform 0.2s;
          display: flex;
          align-items: center;
        }

        .toggle.open {
          transform: rotate(180deg);
        }

        .bot-metrics {
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 20px;
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

          .stats-cards {
            grid-template-columns: repeat(2, 1fr);
          }

          .bot-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 10px;
          }

          .bot-header h3 {
            width: 100%;
          }
        }
      `}</style>
    </div>
  );
}
