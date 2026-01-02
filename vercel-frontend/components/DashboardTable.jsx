/**
 * /components/DashboardTable.jsx
 * Displays transactions in a table format
 */

export default function DashboardTable({ data = [] }) {
  if (!data || data.length === 0) {
    return (
      <div className="empty-state">
        <p>No transactions found</p>
      </div>
    );
  }

  return (
    <div className="table-container">
      <table className="dashboard-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Quantity</th>
            <th>Price</th>
            <th>Total</th>
            <th>Type</th>
            <th>Date</th>
          </tr>
        </thead>
        <tbody>
          {data.map((transaction) => (
            <tr key={transaction.id || Math.random()}>
              <td className="symbol">{transaction.symbol}</td>
              <td className="quantity">{transaction.quantity}</td>
              <td className="price">${transaction.price?.toFixed(2)}</td>
              <td className="total">
                ${(transaction.quantity * transaction.price)?.toFixed(2)}
              </td>
              <td className={`type ${transaction.type}`}>
                {transaction.type?.toUpperCase()}
              </td>
              <td className="date">
                {new Date(transaction.transaction_date).toLocaleDateString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <style jsx>{`
        .table-container {
          overflow-x: auto;
          margin-top: 20px;
        }

        .dashboard-table {
          width: 100%;
          border-collapse: collapse;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          border-radius: 8px;
          overflow: hidden;
        }

        .dashboard-table thead {
          background-color: #f5f5f5;
          border-bottom: 2px solid #ddd;
        }

        .dashboard-table th {
          padding: 12px 15px;
          text-align: left;
          font-weight: 600;
          color: #333;
          font-size: 14px;
        }

        .dashboard-table td {
          padding: 12px 15px;
          border-bottom: 1px solid #eee;
          font-size: 14px;
        }

        .dashboard-table tbody tr:hover {
          background-color: #f9f9f9;
        }

        .dashboard-table tbody tr:last-child td {
          border-bottom: none;
        }

        .symbol {
          font-weight: 600;
          color: #2c3e50;
        }

        .type {
          font-weight: 500;
          padding: 4px 8px;
          border-radius: 4px;
          text-align: center;
        }

        .type.buy {
          background-color: #d4edda;
          color: #155724;
        }

        .type.sell {
          background-color: #f8d7da;
          color: #721c24;
        }

        .price,
        .quantity,
        .total {
          text-align: right;
          font-family: 'Courier New', monospace;
        }

        .date {
          font-size: 13px;
          color: #666;
        }

        .empty-state {
          padding: 40px 20px;
          text-align: center;
          color: #999;
          border: 2px dashed #ddd;
          border-radius: 8px;
          margin-top: 20px;
        }

        .empty-state p {
          margin: 0;
          font-size: 16px;
        }
      `}</style>
    </div>
  );
}
