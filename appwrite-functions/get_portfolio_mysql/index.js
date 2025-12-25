/**
 * Get User Portfolio from MySQL
 * 
 * This function queries MySQL database for user's portfolio holdings
 * Acts as bridge between Streamlit frontend and MySQL backend
 */

const mysql = require('mysql2/promise');

module.exports = async ({ req, res, log, error }) => {
  try {
    // Parse request body
    const body = req.bodyJson || {};
    const { user_id, action } = body;

    if (!user_id) {
      return res.json({ error: 'user_id is required' }, 400);
    }

    // MySQL connection config
    const connection = await mysql.createConnection({
      host: process.env.MYSQL_HOST || 'localhost',
      port: parseInt(process.env.MYSQL_PORT || '3306'),
      user: process.env.MYSQL_USER,
      password: process.env.MYSQL_PASSWORD,
      database: process.env.MYSQL_DATABASE || 'mansa_bot'
    });

    let result;

    // Handle different actions
    switch (action) {
      case 'get_holdings':
        // Get portfolio holdings
        const [holdings] = await connection.execute(
          `SELECT 
            ticker,
            SUM(quantity) as total_quantity,
            AVG(purchase_price) as avg_cost_basis,
            SUM(total_value) as total_invested
          FROM portfolios
          WHERE user_id = ?
          GROUP BY ticker
          HAVING total_quantity > 0`,
          [user_id]
        );
        result = { holdings, user_id };
        break;

      case 'get_summary':
        // Get portfolio summary
        const [summary] = await connection.execute(
          `SELECT 
            COUNT(DISTINCT ticker) as total_positions,
            SUM(total_value) as total_invested,
            SUM(quantity * current_price) as current_value,
            (SUM(quantity * current_price) - SUM(total_value)) as unrealized_pnl
          FROM portfolios
          WHERE user_id = ?`,
          [user_id]
        );
        result = { summary: summary[0], user_id };
        break;

      case 'get_transactions':
        // Get transaction history
        const limit = body.limit || 100;
        const [transactions] = await connection.execute(
          `SELECT 
            transaction_id,
            ticker,
            transaction_type,
            quantity,
            price,
            total_value,
            transaction_date
          FROM transactions
          WHERE user_id = ?
          ORDER BY transaction_date DESC
          LIMIT ?`,
          [user_id, limit]
        );
        result = { transactions, user_id };
        break;

      default:
        // Default: get holdings
        const [defaultHoldings] = await connection.execute(
          `SELECT ticker, SUM(quantity) as quantity 
           FROM portfolios 
           WHERE user_id = ? 
           GROUP BY ticker`,
          [user_id]
        );
        result = { holdings: defaultHoldings, user_id };
    }

    await connection.end();

    log('Portfolio query successful');
    return res.json(result);

  } catch (err) {
    error('MySQL query failed: ' + err.message);
    return res.json({ 
      error: 'Failed to fetch portfolio data',
      details: err.message 
    }, 500);
  }
};
