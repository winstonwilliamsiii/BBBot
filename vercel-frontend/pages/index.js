/**
 * /pages/index.js
 * Landing / home page
 */

import { useEffect, useState } from 'react';

import Link from 'next/link';

export default function Home() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch('/api/health');
        const data = await response.json();
        setHealth(data);
      } catch (error) {
        setHealth({ status: 'error', message: error.message });
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
  }, []);

  return (
    <div className="home">
      <header className="header">
        <h1>Bentley Budget Bot</h1>
        <p className="subtitle">AI-Powered Portfolio Management</p>
      </header>

      <main className="main">
        <div className="hero">
          <h2>Welcome to Your Financial Dashboard</h2>
          <p>Monitor your portfolio, track investments, and manage payments all in one place.</p>
        </div>

        <div className="grid">
          <Link href="/dashboard" className="card">
            <div className="card-content">
              <h3>📊 Dashboard</h3>
              <p>View your transactions and portfolio overview</p>
            </div>
          </Link>

          <Link href="/metrics" className="card">
            <div className="card-content">
              <h3>📈 ML Metrics</h3>
              <p>Monitor bot performance and ML experiment results</p>
            </div>
          </Link>

          <Link href="/watchlist" className="card">
            <div className="card-content">
              <h3>⭐ Watchlist</h3>
              <p>Track stocks and build your personalized watchlist</p>
            </div>
          </Link>

          <Link href="/payments" className="card">
            <div className="card-content">
              <h3>💳 Payments</h3>
              <p>Create and manage payment transactions</p>
            </div>
          </Link>
        </div>

        <div className="status">
          <h3>System Status</h3>
          {loading ? (
            <p className="loading">Checking system health...</p>
          ) : health?.status === 'healthy' ? (
            <div className="status-card healthy">
              <span className="indicator">●</span>
              <div>
                <p><strong>Status:</strong> Operational</p>
                <p className="small">All systems functioning normally</p>
              </div>
            </div>
          ) : (
            <div className="status-card error">
              <span className="indicator">●</span>
              <div>
                <p><strong>Status:</strong> {health?.message || 'Unavailable'}</p>
                <p className="small">Please try again later</p>
              </div>
            </div>
          )}
        </div>

        <div className="info">
          <h3>Quick Start</h3>
          <ol>
            <li>Go to the <Link href="/dashboard">Dashboard</Link> to see your transactions</li>
            <li>Add stocks to your <Link href="/watchlist">Watchlist</Link> for monitoring</li>
            <li>Create <Link href="/payments">Payments</Link> to record transactions</li>
            <li>Check <Link href="/metrics">ML Metrics</Link> for bot performance data</li>
          </ol>
        </div>
      </main>

      <style jsx>{`
        .home {
          min-height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 20px;
        }

        .header {
          text-align: center;
          padding: 40px 20px;
        }

        .header h1 {
          font-size: 48px;
          margin: 0 0 10px 0;
          font-weight: 700;
        }

        .subtitle {
          font-size: 18px;
          margin: 0;
          opacity: 0.9;
        }

        .main {
          max-width: 1200px;
          margin: 0 auto;
          padding: 40px 20px;
        }

        .hero {
          text-align: center;
          margin-bottom: 50px;
        }

        .hero h2 {
          font-size: 32px;
          margin: 0 0 15px 0;
        }

        .hero p {
          font-size: 16px;
          opacity: 0.9;
          margin: 0;
        }

        .grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
          margin-bottom: 50px;
        }

        .card {
          background-color: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 12px;
          padding: 25px;
          text-decoration: none;
          color: white;
          transition: all 0.3s ease;
          cursor: pointer;
        }

        .card:hover {
          background-color: rgba(255, 255, 255, 0.15);
          transform: translateY(-5px);
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }

        .card-content h3 {
          margin: 0 0 10px 0;
          font-size: 20px;
        }

        .card-content p {
          margin: 0;
          font-size: 14px;
          opacity: 0.9;
        }

        .status {
          background-color: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 12px;
          padding: 25px;
          margin-bottom: 30px;
        }

        .status h3 {
          margin: 0 0 15px 0;
          font-size: 18px;
        }

        .loading {
          opacity: 0.8;
          font-size: 14px;
          margin: 0;
        }

        .status-card {
          display: flex;
          align-items: flex-start;
          gap: 15px;
          padding: 15px;
          border-radius: 8px;
          background-color: rgba(0, 0, 0, 0.1);
        }

        .status-card.healthy {
          border-left: 4px solid #4caf50;
        }

        .status-card.error {
          border-left: 4px solid #f44336;
        }

        .indicator {
          font-size: 20px;
          margin-top: 2px;
        }

        .status-card p {
          margin: 5px 0;
        }

        .status-card .small {
          font-size: 13px;
          opacity: 0.8;
        }

        .info {
          background-color: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 12px;
          padding: 25px;
        }

        .info h3 {
          margin: 0 0 15px 0;
          font-size: 18px;
        }

        .info ol {
          margin: 0;
          padding-left: 20px;
        }

        .info li {
          margin-bottom: 10px;
          line-height: 1.6;
        }

        .info a {
          color: #fff;
          text-decoration: underline;
        }

        .info a:hover {
          opacity: 0.8;
        }

        @media (max-width: 768px) {
          .header h1 {
            font-size: 32px;
          }

          .hero h2 {
            font-size: 24px;
          }

          .grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}
