/**
 * /components/MetricsChart.jsx
 * Displays bot metrics and ML experiment results
 */

import React from 'react';

export default function MetricsChart({ data = {}, stats = null }) {
  const metrics = data.metrics || {};
  
  const renderMetric = (label, value, format = 'number') => {
    let displayValue = value;
    
    if (format === 'percentage') {
      displayValue = `${(value * 100).toFixed(2)}%`;
    } else if (format === 'currency') {
      displayValue = `$${value?.toFixed(2)}`;
    } else if (format === 'number') {
      displayValue = value?.toFixed(4);
    }

    return (
      <div className="metric-item" key={label}>
        <div className="metric-label">{label}</div>
        <div className="metric-value">{displayValue}</div>
      </div>
    );
  };

  if (!data || Object.keys(metrics).length === 0) {
    return (
      <div className="empty-metrics">
        <p>No metrics data available</p>
      </div>
    );
  }

  return (
    <div className="metrics-container">
      <div className="metrics-header">
        <h2>Bot Metrics</h2>
        {data.experiment_id && (
          <span className="experiment-id">Exp: {data.experiment_id}</span>
        )}
      </div>

      <div className="metrics-grid">
        {Object.entries(metrics).map(([key, value]) => {
          // Determine format based on key name
          let format = 'number';
          if (key.includes('ratio') || key === 'sharpe') format = 'number';
          if (key.includes('rate') || key.includes('accuracy')) format = 'percentage';
          if (key.includes('return') || key.includes('drawdown')) format = 'percentage';
          
          return renderMetric(
            key.replace(/_/g, ' ').toUpperCase(),
            value,
            format
          );
        })}
      </div>

      {stats && (
        <div className="metrics-stats">
          <h3>Statistics</h3>
          <div className="stats-grid">
            {Object.entries(stats).map(([key, value]) => (
              <div className="stat-item" key={key}>
                <span className="stat-label">{key.replace(/_/g, ' ')}:</span>
                <span className="stat-value">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.status && (
        <div className={`status-badge status-${data.status}`}>
          Status: {data.status.toUpperCase()}
        </div>
      )}

      <style jsx>{`
        .metrics-container {
          padding: 20px;
          background-color: #f9f9f9;
          border-radius: 8px;
          margin-top: 20px;
        }

        .metrics-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 15px;
          border-bottom: 2px solid #ddd;
        }

        .metrics-header h2 {
          margin: 0;
          color: #333;
        }

        .experiment-id {
          background-color: #e3f2fd;
          color: #1976d2;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          margin-bottom: 20px;
        }

        .metric-item {
          background-color: white;
          padding: 15px;
          border-radius: 6px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
          border-left: 4px solid #2c3e50;
        }

        .metric-label {
          font-size: 12px;
          color: #666;
          text-transform: uppercase;
          font-weight: 600;
          margin-bottom: 8px;
          letter-spacing: 0.5px;
        }

        .metric-value {
          font-size: 24px;
          font-weight: 700;
          color: #2c3e50;
          font-family: 'Courier New', monospace;
        }

        .metrics-stats {
          background-color: white;
          padding: 15px;
          border-radius: 6px;
          margin-bottom: 15px;
        }

        .metrics-stats h3 {
          margin-top: 0;
          margin-bottom: 12px;
          color: #333;
          font-size: 14px;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 12px;
        }

        .stat-item {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid #eee;
          font-size: 13px;
        }

        .stat-label {
          color: #666;
          font-weight: 500;
        }

        .stat-value {
          color: #333;
          font-weight: 600;
          font-family: 'Courier New', monospace;
        }

        .status-badge {
          display: inline-block;
          padding: 8px 16px;
          border-radius: 4px;
          font-weight: 600;
          font-size: 12px;
          margin-top: 10px;
        }

        .status-completed {
          background-color: #d4edda;
          color: #155724;
        }

        .status-failed {
          background-color: #f8d7da;
          color: #721c24;
        }

        .status-in_progress {
          background-color: #fff3cd;
          color: #856404;
        }

        .empty-metrics {
          padding: 40px 20px;
          text-align: center;
          color: #999;
          border: 2px dashed #ddd;
          border-radius: 8px;
        }

        .empty-metrics p {
          margin: 0;
          font-size: 16px;
        }
      `}</style>
    </div>
  );
}
