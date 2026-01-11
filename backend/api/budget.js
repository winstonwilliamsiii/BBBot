/**
 * Budget API Endpoint for Bentley Budget Bot
 * Handles budget-related operations and calculations
 */
// api/budget.js

import mysql from 'mysql2/promise';

export default async function handler(req, res) {
  try {
    // Set CORS headers
    res.setHeader('Access-Control-Allow-Credentials', true);
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    // Handle OPTIONS preflight
    if (req.method === 'OPTIONS') {
      return res.status(200).end();
    }

    // Route based on method
    switch (req.method) {
      case 'GET':
        return await global.handleGetBudget(req, res);
      case 'POST':
        return await global.handleCreateBudget(req, res);
      case 'PUT':
        return await global.handleUpdateBudget(req, res);
      case 'DELETE':
        return await global.handleDeleteBudget(req, res);
      default:
        res.setHeader('Allow', ['GET', 'POST', 'PUT', 'DELETE']);
        return res.status(405).json({ error: `Method ${req.method} Not Allowed` });
    }
  } catch (error) {
    console.error('Budget API Error:', error);
    return res.status(500).json({
      error: 'Internal Server Error',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
}
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
        await handleGetBudget(req, res);
        break;
      case 'POST':
        await handleCreateBudget(req, res);
        break;
      case 'PUT':
        await handleUpdateBudget(req, res);
        break;
      case 'DELETE':
        await handleDeleteBudget(req, res);
        break;
      default:
        res.setHeader('Allow', ['GET', 'POST', 'PUT', 'DELETE']);
        res.status(405).json({ error: `Method ${method} Not Allowed` });
    }
  } catch (error) {
    console.error('Budget API Error:', error);
    res.status(500).json({ 
      error: 'Internal Server Error',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
}

// Get budget data
async function handleGetBudget(req, res) {
  const { budgetId, userId } = req.query;
  
  // Sample budget data structure
  const sampleBudget = {
    id: budgetId || '1',
    userId: userId || 'user_123',
    name: 'Monthly Budget',
    totalIncome: 5000,
    totalExpenses: 3500,
    categories: [
      { name: 'Housing', budgeted: 1500, spent: 1450, remaining: 50 },
      { name: 'Food', budgeted: 600, spent: 550, remaining: 50 },
      { name: 'Transportation', budgeted: 400, spent: 380, remaining: 20 },
      { name: 'Entertainment', budgeted: 300, spent: 320, remaining: -20 },
      { name: 'Savings', budgeted: 1000, spent: 800, remaining: 200 }
    ],
    period: {
      start: '2024-11-01',
      end: '2024-11-30'
    },
    createdAt: '2024-11-01T00:00:00Z',
    updatedAt: new Date().toISOString()
  };

  res.status(200).json({
    success: true,
    data: sampleBudget,
    message: 'Budget retrieved successfully'
  });
}

// Create new budget
async function handleCreateBudget(req, res) {
  const { name, income, categories } = req.body;
  
  if (!name || !income) {
    return res.status(400).json({
      error: 'Bad Request',
      message: 'Name and income are required fields'
    });
  }

  const newBudget = {
    id: Date.now().toString(),
    userId: req.body.userId || 'user_123',
    name,
    totalIncome: income,
    totalExpenses: 0,
    categories: categories || [],
    period: {
      start: new Date().toISOString().split('T')[0],
      end: new Date(new Date().getTime() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };

  res.status(201).json({
    success: true,
    data: newBudget,
    message: 'Budget created successfully'
  });
}

// Update existing budget
async function handleUpdateBudget(req, res) {
  const { budgetId } = req.query;
  const updateData = req.body;
  
  if (!budgetId) {
    return res.status(400).json({
      error: 'Bad Request',
      message: 'Budget ID is required'
    });
  }

  const updatedBudget = {
    id: budgetId,
    ...updateData,
    updatedAt: new Date().toISOString()
  };

  res.status(200).json({
    success: true,
    data: updatedBudget,
    message: 'Budget updated successfully'
  });
}

// Delete budget
async function handleDeleteBudget(req, res) {
  const { budgetId } = req.query;
  
  if (!budgetId) {
    return res.status(400).json({
      error: 'Bad Request',
      message: 'Budget ID is required'
    });
  }

  res.status(200).json({
    success: true,
    message: `Budget ${budgetId} deleted successfully`
  });
}
