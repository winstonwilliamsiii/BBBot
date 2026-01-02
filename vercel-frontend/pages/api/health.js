/**
 * /pages/api/health.js
 * Health check endpoint for monitoring API and Appwrite connectivity
 */

export default async function handler(req, res) {
  try {
    const endpoint = process.env.NEXT_PUBLIC_APPWRITE_ENDPOINT;
    const projectId = process.env.NEXT_PUBLIC_APPWRITE_PROJECT_ID;

    // Check if critical env vars are set
    const appwriteConfigured = !!(endpoint && projectId);

    // Attempt to ping Appwrite health endpoint
    let appwriteHealth = false;
    if (appwriteConfigured) {
      try {
        const response = await fetch(`${endpoint}/health`, {
          method: 'GET',
          timeout: 5000
        });
        appwriteHealth = response.ok;
      } catch (error) {
        console.warn('Appwrite health check failed:', error.message);
        appwriteHealth = false;
      }
    }

    // Build status response
    const status = {
      timestamp: new Date().toISOString(),
      service: 'bentley-budget-bot-vercel',
      version: process.env.npm_package_version || '1.0.0',
      uptime: process.uptime(),
      environment: process.env.NODE_ENV,
      
      dependencies: {
        appwrite: {
          configured: appwriteConfigured,
          healthy: appwriteHealth,
          endpoint: endpoint ? 'set' : 'missing',
          projectId: projectId ? 'set' : 'missing'
        },
        nodeEnv: process.env.NODE_ENV === 'production' ? 'production' : 'development'
      },

      features: {
        secureApiRoutes: true,
        auditLogging: true,
        botMetricsTracking: true,
        transactionManagement: true,
        paymentProcessing: true
      }
    };

    // Return appropriate status code based on health
    const statusCode = appwriteHealth ? 200 : 503;

    return res.status(statusCode).json({
      status: appwriteHealth ? 'healthy' : 'degraded',
      ...status
    });

  } catch (error) {
    console.error('Health check error:', error);
    
    return res.status(500).json({
      status: 'error',
      error: 'Health check failed',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
}
