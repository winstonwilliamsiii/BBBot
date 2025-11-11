/**
 * Zapier Triggers API Endpoint for Bentley Budget Bot
 * Handles webhook integrations and automation triggers
 */

export default async function handler(req, res) {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Credentials', true);
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS,PATCH,DELETE,POST,PUT');
  res.setHeader('Access-Control-Allow-Headers', 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization');

  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  const { method } = req;

  try {
    switch (method) {
      case 'GET':
        await handleGetTriggers(req, res);
        break;
      case 'POST':
        await handleZapierWebhook(req, res);
        break;
      case 'PUT':
        await handleUpdateTrigger(req, res);
        break;
      case 'DELETE':
        await handleDeleteTrigger(req, res);
        break;
      default:
        res.setHeader('Allow', ['GET', 'POST', 'PUT', 'DELETE']);
        res.status(405).json({ error: `Method ${method} Not Allowed` });
    }
  } catch (error) {
    console.error('Zapier Triggers API Error:', error);
    res.status(500).json({ 
      error: 'Internal Server Error',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
}

// Get available triggers and webhooks
async function handleGetTriggers(req, res) {
  const { userId, type } = req.query;
  
  // Available trigger types and their configurations
  const triggerTypes = {
    'new-transaction': {
      id: 'new-transaction',
      name: 'New Transaction Added',
      description: 'Triggered when a new transaction is created',
      fields: [
        { key: 'amount', label: 'Transaction Amount', type: 'number' },
        { key: 'description', label: 'Description', type: 'string' },
        { key: 'category', label: 'Category', type: 'string' },
        { key: 'date', label: 'Transaction Date', type: 'datetime' }
      ]
    },
    'budget-exceeded': {
      id: 'budget-exceeded',
      name: 'Budget Limit Exceeded',
      description: 'Triggered when spending exceeds budget limit in a category',
      fields: [
        { key: 'category', label: 'Budget Category', type: 'string' },
        { key: 'budgetLimit', label: 'Budget Limit', type: 'number' },
        { key: 'currentSpending', label: 'Current Spending', type: 'number' },
        { key: 'excessAmount', label: 'Excess Amount', type: 'number' }
      ]
    },
    'monthly-report': {
      id: 'monthly-report',
      name: 'Monthly Financial Report',
      description: 'Triggered at the end of each month with financial summary',
      fields: [
        { key: 'totalIncome', label: 'Total Income', type: 'number' },
        { key: 'totalExpenses', label: 'Total Expenses', type: 'number' },
        { key: 'netSavings', label: 'Net Savings', type: 'number' },
        { key: 'reportPeriod', label: 'Report Period', type: 'string' }
      ]
    },
    'low-balance': {
      id: 'low-balance',
      name: 'Low Account Balance Alert',
      description: 'Triggered when account balance falls below threshold',
      fields: [
        { key: 'accountName', label: 'Account Name', type: 'string' },
        { key: 'currentBalance', label: 'Current Balance', type: 'number' },
        { key: 'threshold', label: 'Alert Threshold', type: 'number' },
        { key: 'alertLevel', label: 'Alert Level', type: 'string' }
      ]
    }
  };

  // Active webhooks for the user
  const activeWebhooks = [
    {
      id: 'webhook_1',
      userId: userId || 'user_123',
      triggerType: 'new-transaction',
      webhookUrl: 'https://hooks.zapier.com/hooks/catch/example1/',
      isActive: true,
      createdAt: '2024-11-01T10:00:00Z',
      lastTriggered: '2024-11-07T15:30:00Z'
    },
    {
      id: 'webhook_2',
      userId: userId || 'user_123',
      triggerType: 'budget-exceeded',
      webhookUrl: 'https://hooks.zapier.com/hooks/catch/example2/',
      isActive: true,
      createdAt: '2024-11-01T10:00:00Z',
      lastTriggered: null
    }
  ];

  if (type && triggerTypes[type]) {
    res.status(200).json({
      success: true,
      data: {
        trigger: triggerTypes[type],
        webhooks: activeWebhooks.filter(w => w.triggerType === type)
      },
      message: 'Trigger information retrieved successfully'
    });
  } else {
    res.status(200).json({
      success: true,
      data: {
        availableTriggers: Object.values(triggerTypes),
        activeWebhooks,
        totalWebhooks: activeWebhooks.length
      },
      message: 'All triggers and webhooks retrieved successfully'
    });
  }
}

// Handle incoming Zapier webhook
async function handleZapierWebhook(req, res) {
  const { triggerType, webhookUrl, userId } = req.body;
  const webhookData = req.body.data || {};
  
  // Validate required fields
  if (!triggerType) {
    return res.status(400).json({
      error: 'Bad Request',
      message: 'triggerType is required'
    });
  }

  // Process different trigger types
  let processedData = {};
  
  switch (triggerType) {
    case 'new-transaction':
      processedData = await processNewTransactionTrigger(webhookData);
      break;
      
    case 'budget-exceeded':
      processedData = await processBudgetExceededTrigger(webhookData);
      break;
      
    case 'monthly-report':
      processedData = await processMonthlyReportTrigger(webhookData);
      break;
      
    case 'low-balance':
      processedData = await processLowBalanceTrigger(webhookData);
      break;
      
    default:
      return res.status(400).json({
        error: 'Bad Request',
        message: `Unknown trigger type: ${triggerType}`
      });
  }

  // Log the webhook trigger
  const webhookLog = {
    id: Date.now().toString(),
    userId: userId || 'user_123',
    triggerType,
    webhookUrl: webhookUrl || 'internal',
    data: processedData,
    timestamp: new Date().toISOString(),
    status: 'processed'
  };

  res.status(200).json({
    success: true,
    data: {
      log: webhookLog,
      processedData
    },
    message: `${triggerType} webhook processed successfully`
  });
}

// Update webhook configuration
async function handleUpdateTrigger(req, res) {
  const { webhookId } = req.query;
  const updateData = req.body;
  
  if (!webhookId) {
    return res.status(400).json({
      error: 'Bad Request',
      message: 'Webhook ID is required'
    });
  }

  const updatedWebhook = {
    id: webhookId,
    ...updateData,
    updatedAt: new Date().toISOString()
  };

  res.status(200).json({
    success: true,
    data: updatedWebhook,
    message: 'Webhook updated successfully'
  });
}

// Delete webhook
async function handleDeleteTrigger(req, res) {
  const { webhookId } = req.query;
  
  if (!webhookId) {
    return res.status(400).json({
      error: 'Bad Request',
      message: 'Webhook ID is required'
    });
  }

  res.status(200).json({
    success: true,
    message: `Webhook ${webhookId} deleted successfully`
  });
}

// Trigger processing functions
async function processNewTransactionTrigger(data) {
  return {
    triggerType: 'new-transaction',
    transaction: {
      amount: data.amount || 0,
      description: data.description || 'New transaction',
      category: data.category || 'Other',
      date: data.date || new Date().toISOString()
    },
    timestamp: new Date().toISOString()
  };
}

async function processBudgetExceededTrigger(data) {
  return {
    triggerType: 'budget-exceeded',
    alert: {
      category: data.category || 'Unknown',
      budgetLimit: data.budgetLimit || 0,
      currentSpending: data.currentSpending || 0,
      excessAmount: (data.currentSpending || 0) - (data.budgetLimit || 0),
      severity: data.excessAmount > 100 ? 'high' : 'medium'
    },
    timestamp: new Date().toISOString()
  };
}

async function processMonthlyReportTrigger(data) {
  return {
    triggerType: 'monthly-report',
    report: {
      totalIncome: data.totalIncome || 0,
      totalExpenses: data.totalExpenses || 0,
      netSavings: (data.totalIncome || 0) - (data.totalExpenses || 0),
      reportPeriod: data.reportPeriod || new Date().toISOString().slice(0, 7)
    },
    timestamp: new Date().toISOString()
  };
}

async function processLowBalanceTrigger(data) {
  return {
    triggerType: 'low-balance',
    alert: {
      accountName: data.accountName || 'Unknown Account',
      currentBalance: data.currentBalance || 0,
      threshold: data.threshold || 100,
      alertLevel: data.currentBalance < 50 ? 'critical' : 'warning'
    },
    timestamp: new Date().toISOString()
  };
}