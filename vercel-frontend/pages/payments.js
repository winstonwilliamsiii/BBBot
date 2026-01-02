/**
 * /pages/payments.js
 * Payments page - create and manage payments
 */

import { useEffect, useState } from 'react';

import PaymentForm from '../components/PaymentForm';

export default function Payments() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalPayments: 0,
    totalAmount: 0,
    averageAmount: 0
  });

  useEffect(() => {
    fetchPayments();
  }, []);

  const fetchPayments = async () => {
    setLoading(true);

    try {
      // Try to fetch payments from API or initialize empty
      const response = await fetch('/api/health');
      if (response.ok) {
        // For now, initialize with empty payments
        // In production, fetch from Appwrite
        setPayments([]);
      }
    } catch (err) {
      console.error('Error fetching payments:', err);
      setPayments([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentCreated = (payment) => {
    // Add new payment to list
    setPayments(prev => [payment, ...prev]);
    
    // Recalculate stats
    const newStats = {
      totalPayments: payments.length + 1,
      totalAmount: payments.reduce((sum, p) => sum + (p.amount || 0), 0) + (payment.amount || 0),
      averageAmount: 0
    };
    newStats.averageAmount = newStats.totalAmount / newStats.totalPayments;
    setStats(newStats);
  };

  return (
    <div className="payments-page">
      <header className="page-header">
        <h1>Payments</h1>
        <p>Create and manage payment transactions</p>
      </header>

      <main className="page-main">
        {/* Statistics */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Total Payments</div>
            <div className="stat-value">{stats.totalPayments}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Total Amount</div>
            <div className="stat-value">${stats.totalAmount.toFixed(2)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Average Payment</div>
            <div className="stat-value">${stats.averageAmount.toFixed(2)}</div>
          </div>
        </div>

        {/* Payment Form */}
        <PaymentForm onSubmit={handlePaymentCreated} />

        {/* Recent Payments */}
        {payments.length > 0 && (
          <div className="recent-payments">
            <h2>Recent Payments</h2>
            <div className="payments-list">
              {payments.map((payment, index) => (
                <div key={index} className="payment-item">
                  <div className="payment-info">
                    <div className="payment-amount">${payment.amount?.toFixed(2)}</div>
                    <div className="payment-details">
                      <div className="method">{payment.payment_method}</div>
                      {payment.description && <div className="description">{payment.description}</div>}
                    </div>
                  </div>
                  <div className="payment-date">
                    {payment.created_at ? new Date(payment.created_at).toLocaleDateString() : 'Just now'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      <style jsx>{`
        .payments-page {
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
          max-width: 800px;
          margin: 0 auto;
          padding: 30px 20px;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 20px;
          margin-bottom: 40px;
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
          font-size: 24px;
          font-weight: 700;
          color: #333;
        }

        .recent-payments {
          background-color: white;
          border-radius: 8px;
          padding: 20px;
          margin-top: 40px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .recent-payments h2 {
          margin: 0 0 20px 0;
          color: #333;
          font-size: 18px;
        }

        .payments-list {
          display: flex;
          flex-direction: column;
          gap: 15px;
        }

        .payment-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 15px;
          border-bottom: 1px solid #eee;
          transition: background-color 0.2s;
        }

        .payment-item:hover {
          background-color: #f9f9f9;
        }

        .payment-item:last-child {
          border-bottom: none;
        }

        .payment-info {
          display: flex;
          gap: 15px;
          align-items: flex-start;
          flex: 1;
        }

        .payment-amount {
          font-size: 18px;
          font-weight: 700;
          color: #28a745;
          min-width: 80px;
        }

        .payment-details {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }

        .method {
          font-size: 14px;
          color: #333;
          font-weight: 600;
          text-transform: capitalize;
        }

        .description {
          font-size: 13px;
          color: #999;
        }

        .payment-date {
          font-size: 12px;
          color: #999;
          white-space: nowrap;
          margin-left: 20px;
        }

        @media (max-width: 768px) {
          .page-header h1 {
            font-size: 28px;
          }

          .stats-grid {
            grid-template-columns: 1fr;
          }

          .payment-item {
            flex-direction: column;
            align-items: flex-start;
            gap: 10px;
          }

          .payment-date {
            margin-left: 0;
          }
        }
      `}</style>
    </div>
  );
}
