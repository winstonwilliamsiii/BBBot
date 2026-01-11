/**
 * Transactions API Endpoint for Bentley Budget Bot
 * Handles transaction management and analysis
 */

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  const { method } = req;

  try {
    switch (method) {
      case 'GET':
        await handleGetTransactions(req, res);
        break;
      case 'POST':
        await handleCreateTransaction(req, res);
        break;
      case 'PUT':
        await handleUpdateTransaction(req, res);
        break;
      case 'DELETE':
        await handleDeleteTransaction(req, res);
        break;
      default:
        res.setHeader('Allow', ['GET', 'POST', 'PUT', 'DELETE']);
        res.status(405).json({ error: `Method ${method} Not Allowed` });
    }
  } catch (error) {
    console.error('Transactions API Error:', error);
    res.status(500).json({ 
      error: 'Internal Server Error',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
}

// Get transactions
async function handleGetTransactions(req, res) {
  const { userId, category, startDate, endDate, limit = 50, offset = 0 } = req.query;
  
  // Sample transactions data
  const sampleTransactions = [
    {
      id: '1',
      userId: userId || 'user_123',
      amount: -85.50,
      description: 'Grocery Store Purchase',
      category: 'Food',
      date: '2024-11-07',
      type: 'expense',
      merchant: 'Whole Foods Market',
      account: 'Checking',
      tags: ['groceries', 'food'],
      createdAt: '2024-11-07T14:30:00Z'
    },
    {
      id: '2',
      userId: userId || 'user_123',
      amount: -45.00,
      description: 'Gas Station',
      category: 'Transportation',
      date: '2024-11-06',
      type: 'expense',
      merchant: 'Shell Gas Station',
      account: 'Credit Card',
      tags: ['gas', 'transportation'],
      createdAt: '2024-11-06T09:15:00Z'
    },
    {
      id: '3',
      userId: userId || 'user_123',
      amount: 2500.00,
      description: 'Salary Deposit',
      category: 'Income',
      date: '2024-11-01',
      type: 'income',
      merchant: 'Employer Inc.',
      account: 'Checking',
      tags: ['salary', 'income'],
      createdAt: '2024-11-01T08:00:00Z'
    },
    {
      id: '4',
      userId: userId || 'user_123',
      amount: -1200.00,
      description: 'Monthly Rent',
      category: 'Housing',
      date: '2024-11-01',
      type: 'expense',
      merchant: 'Property Management Co.',
      account: 'Checking',
      tags: ['rent', 'housing'],
      createdAt: '2024-11-01T10:00:00Z'
    },
    {
      id: '5',
      userId: userId || 'user_123',
      amount: -25.99,
      description: 'Netflix Subscription',
      category: 'Entertainment',
      date: '2024-11-05',
      type: 'expense',
      merchant: 'Netflix',
      account: 'Credit Card',
      tags: ['subscription', 'entertainment'],
      createdAt: '2024-11-05T12:00:00Z'
    }
  ];

  // Filter transactions based on query parameters
  let filteredTransactions = sampleTransactions;
  
  if (category) {
    filteredTransactions = filteredTransactions.filter(t => 
      t.category.toLowerCase() === category.toLowerCase()
    );
  }
  
  if (startDate) {
    filteredTransactions = filteredTransactions.filter(t => t.date >= startDate);
  }
  
  if (endDate) {
    filteredTransactions = filteredTransactions.filter(t => t.date <= endDate);
  }

  // Apply pagination
  const paginatedTransactions = filteredTransactions.slice(
    parseInt(offset), 
    parseInt(offset) + parseInt(limit)
  );

  // Calculate summary statistics
  const totalIncome = filteredTransactions
    .filter(t => t.type === 'income')
    .reduce((sum, t) => sum + t.amount, 0);
    
  const totalExpenses = Math.abs(filteredTransactions
    .filter(t => t.type === 'expense')
    .reduce((sum, t) => sum + t.amount, 0));

  const netAmount = totalIncome - totalExpenses;

  res.status(200).json({
    success: true,
    data: {
      transactions: paginatedTransactions,
      pagination: {
        limit: parseInt(limit),
        offset: parseInt(offset),
        total: filteredTransactions.length
      },
      summary: {
        totalIncome,
        totalExpenses,
        netAmount,
        transactionCount: filteredTransactions.length
      }
    },
    message: 'Transactions retrieved successfully'
  });
}

// Create new transaction
async function handleCreateTransaction(req, res) {
  const { amount, description, category, type, merchant, account } = req.body;
  
  if (!amount || !description || !category || !type) {
    return res.status(400).json({
      error: 'Bad Request',
      message: 'Amount, description, category, and type are required fields'
    });
  }

  const newTransaction = {
    id: Date.now().toString(),
    userId: req.body.userId || 'user_123',
    amount: parseFloat(amount),
    description,
    category,
    type,
    merchant: merchant || '',
    account: account || 'Default',
    date: req.body.date || new Date().toISOString().split('T')[0],
    tags: req.body.tags || [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };

  res.status(201).json({
    success: true,
    data: newTransaction,
    message: 'Transaction created successfully'
  });
}

// Update existing transaction
async function handleUpdateTransaction(req, res) {
  const { transactionId } = req.query;
  const updateData = req.body;
  
  if (!transactionId) {
    return res.status(400).json({
      error: 'Bad Request',
      message: 'Transaction ID is required'
    });
  }

  const updatedTransaction = {
    id: transactionId,
    ...updateData,
    updatedAt: new Date().toISOString()
  };

  res.status(200).json({
    success: true,
    data: updatedTransaction,
    message: 'Transaction updated successfully'
  });
}

// Delete transaction
async function handleDeleteTransaction(req, res) {
  const { transactionId } = req.query;
  
  if (!transactionId) {
    return res.status(400).json({
      error: 'Bad Request',
      message: 'Transaction ID is required'
    });
  }

  res.status(200).json({
    success: true,
    message: `Transaction ${transactionId} deleted successfully`
  });
}