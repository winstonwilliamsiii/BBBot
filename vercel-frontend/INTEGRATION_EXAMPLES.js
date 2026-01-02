/**
 * Example: ML Experiment Integration
 * Shows how to integrate your ML models with the Vercel frontend
 * 
 * This file demonstrates the full workflow:
 * 1. Run ML experiment (Python/Node.js)
 * 2. Send metrics to Vercel API
 * 3. Retrieve and visualize in dashboard
 * 4. Everything is audited and logged
 */

// ============================================
// CLIENT-SIDE COMPONENT (React/Vue/Next.js)
// ============================================

/**
 * Example 1: Dashboard component to display bot metrics
 */
export function BotMetricsDashboard({ userId }) {
  const [metrics, setMetrics] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch(
          `/api/getBotMetrics?user_id=${userId}&include_stats=true`
        );
        const data = await response.json();
        
        setMetrics(data.data);
        setStats(data.stats);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, [userId]);

  if (loading) return <div>Loading metrics...</div>;

  return (
    <div className="metrics-dashboard">
      <h2>Bot Performance Metrics</h2>
      
      {metrics.map((metric) => (
        <div key={metric.id} className="metric-card">
          <h3>{metric.bot_id} - {metric.experiment_id}</h3>
          <p>Accuracy: {metric.metrics.accuracy}</p>
          <p>Sharpe Ratio: {metric.metrics.sharpe_ratio}</p>
          <p>Win Rate: {metric.metrics.win_rate}</p>
          <p>Status: {metric.status}</p>
          <small>Recorded: {new Date(metric.recorded_at).toLocaleString()}</small>
        </div>
      ))}

      {stats && (
        <div className="stats-summary">
          <h3>Summary Statistics</h3>
          <pre>{JSON.stringify(stats, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

/**
 * Example 2: Button to trigger an ML experiment
 */
export function RunExperimentButton({ userId, botId }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const runExperiment = async () => {
    setLoading(true);
    try {
      // Simulate ML experiment or call to Python backend
      const metrics = {
        accuracy: Math.random() * 0.5 + 0.5, // 0.5 - 1.0
        sharpe_ratio: Math.random() * 2,
        max_drawdown: -(Math.random() * 0.2),
        total_return: Math.random() * 0.5,
        win_rate: Math.random() * 0.8 + 0.2,
        trades_executed: Math.floor(Math.random() * 100) + 10
      };

      // Send to Vercel API
      const response = await fetch('/api/recordBotMetrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          bot_id: botId,
          experiment_id: `exp_${Date.now()}`,
          metrics,
          data_source: 'yfinance',
          status: 'completed',
          notes: 'ML experiment completed successfully'
        })
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Experiment failed:', error);
      setResult({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={runExperiment} disabled={loading}>
        {loading ? 'Running Experiment...' : 'Run ML Experiment'}
      </button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}

// ============================================
// PYTHON BACKEND INTEGRATION EXAMPLE
// ============================================

/**
 * Python script to integrate with Vercel API
 * 
 * import requests
 * import json
 * import time
 * from your_ml_model import train_and_evaluate
 * 
 * # Your ML experiment configuration
 * USER_ID = "user123"
 * BOT_ID = "ml_trading_bot_v2"
 * VERCEL_API_BASE = "https://your-vercel-domain.com"
 * 
 * def run_ml_experiment():
 *     # 1. Prepare data (yfinance, MySQL, etc.)
 *     # data = fetch_yfinance_data(['AAPL', 'MSFT', 'GOOGL'])
 *     
 *     # 2. Train model
 *     # model, metrics = train_and_evaluate(data)
 *     
 *     # 3. Record metrics via API
 *     metrics = {
 *         "accuracy": 0.94,
 *         "sharpe_ratio": 1.67,
 *         "max_drawdown": -0.08,
 *         "total_return": 0.42,
 *         "win_rate": 0.71,
 *         "trades_executed": 67
 *     }
 *     
 *     response = requests.post(
 *         f"{VERCEL_API_BASE}/api/recordBotMetrics",
 *         json={
 *             "user_id": USER_ID,
 *             "bot_id": BOT_ID,
 *             "experiment_id": f"exp_{int(time.time())}",
 *             "metrics": metrics,
 *             "data_source": "yfinance",
 *             "status": "completed",
 *             "notes": "Trained on 5 years of historical data"
 *         }
 *     )
 *     
 *     print(f"Metrics recorded: {response.json()}")
 *     return response.json()
 * 
 * # Run the experiment
 * if __name__ == "__main__":
 *     run_ml_experiment()
 */

// ============================================
// FULL WORKFLOW: CURL EXAMPLES
// ============================================

/**
 * 1. Check API Health
 * curl -X GET "https://your-vercel-domain.com/api/health"
 * 
 * 2. Record Bot Metrics
 * curl -X POST "https://your-vercel-domain.com/api/recordBotMetrics" \
 *   -H "Content-Type: application/json" \
 *   -d '{
 *     "user_id": "user123",
 *     "bot_id": "ml_bot_v1",
 *     "experiment_id": "exp_20260101_001",
 *     "metrics": {
 *       "accuracy": 0.92,
 *       "sharpe_ratio": 1.45,
 *       "max_drawdown": -0.12,
 *       "total_return": 0.32,
 *       "win_rate": 0.68,
 *       "trades_executed": 52
 *     },
 *     "data_source": "yfinance",
 *     "status": "completed",
 *     "notes": "ML experiment iteration 5"
 *   }'
 * 
 * 3. Retrieve Bot Metrics
 * curl -X GET "https://your-vercel-domain.com/api/getBotMetrics?user_id=user123&include_stats=true"
 * 
 * 4. Create Transaction
 * curl -X POST "https://your-vercel-domain.com/api/createTransaction" \
 *   -H "Content-Type: application/json" \
 *   -d '{
 *     "user_id": "user123",
 *     "symbol": "AAPL",
 *     "quantity": 10,
 *     "price": 150.00,
 *     "type": "buy",
 *     "transaction_date": "2026-01-01T14:30:00Z"
 *   }'
 * 
 * 5. Create Payment
 * curl -X POST "https://your-vercel-domain.com/api/createPayment" \
 *   -H "Content-Type: application/json" \
 *   -d '{
 *     "user_id": "user123",
 *     "amount": 1000.00,
 *     "currency": "USD",
 *     "description": "Deposit for trading",
 *     "payment_method": "credit_card"
 *   }'
 */

// ============================================
// NEXT.JS API ROUTE PATTERN
// ============================================

/**
 * Template for creating new API routes
 * Save as: /pages/api/newFeature.js
 */

import { callAppwriteFunctionSecure, createAuditLogSecure } from '@/lib/serverAppwriteClient.js';

export default async function handler(req, res) {
  // 1. Check HTTP method
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // 2. Extract and validate input
    const { user_id, data } = req.body;
    
    if (!user_id) {
      return res.status(400).json({ error: 'user_id is required' });
    }

    // 3. Get request context (IP, user agent)
    const userIp = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
    const userAgent = req.headers['user-agent'];

    // 4. Call Appwrite function securely
    const functionId = process.env.NEXT_PUBLIC_APPWRITE_FUNCTION_ID_CUSTOM;
    const result = await callAppwriteFunctionSecure(functionId, {
      user_id,
      data,
      timestamp: new Date().toISOString()
    });

    // 5. Log the action for audit trail
    await createAuditLogSecure({
      user_id,
      action: 'CUSTOM_ACTION',
      entity_type: 'custom_entity',
      entity_id: result?.id || 'unknown',
      changes: { data },
      user_ip: userIp,
      user_agent: userAgent,
      timestamp: new Date().toISOString()
    }).catch(err => console.error('Audit failed:', err));

    // 6. Return success response
    return res.status(200).json({
      success: true,
      data: result,
      message: 'Operation completed successfully'
    });

  } catch (error) {
    console.error('Error:', error);
    return res.status(500).json({
      error: 'Operation failed',
      message: error.message,
      ...(process.env.NODE_ENV === 'development' && { details: error.toString() })
    });
  }
}

export default {};
