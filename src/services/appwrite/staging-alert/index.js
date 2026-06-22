/**
 * Appwrite Function: Staging Alert - Gmail Notifications
 * Purpose: Send Gmail alerts for ML training phase (2-week staging)
 * Triggered by: GitHub Actions migrate-staging.yml workflow
 */

import { Client, Users } from 'node-appwrite';

import nodemailer from 'nodemailer';

export default async ({ req, res, log, error }) => {
  try {
    // Parse incoming payload from GitHub Actions
    const payload = JSON.parse(req.body);
    
    const {
      event,
      status,
      branch,
      commit,
      message,
      recipient,
      phase
    } = payload;

    log(`Staging alert triggered: ${event} - ${status}`);

    // Configure Gmail transporter
    const transporter = nodemailer.createTransport({
      service: 'gmail',
      auth: {
        user: process.env.GMAIL_USER, // Your Gmail address
        pass: process.env.GMAIL_APP_PASSWORD // Gmail app password
      }
    });

    // Determine email subject and body based on event
    let subject, body;

    if (event === 'staging_migration_complete') {
      subject = '🧠 Bentley Bot - ML Training Phase Initiated (2 Weeks)';
      body = `
        <html>
          <head>
            <style>
              body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
              .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }
              .content { padding: 20px; background: #f4f4f4; }
              .card { background: white; padding: 20px; margin: 10px 0; border-left: 4px solid #667eea; }
              .success { color: #10b981; font-weight: bold; }
              .info { color: #3b82f6; }
              .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
            </style>
          </head>
          <body>
            <div class="header">
              <h1>🧠 ML Training Phase Initiated</h1>
            </div>
            <div class="content">
              <div class="card">
                <h2 class="success">✅ Staging Migration Successful</h2>
                <p><strong>Status:</strong> ${message}</p>
                <p><strong>Branch:</strong> ${branch}</p>
                <p><strong>Commit:</strong> <code>${commit}</code></p>
              </div>
              
              <div class="card">
                <h3>📊 Deep Learning Training Phase</h3>
                <p><strong>Duration:</strong> 2 weeks</p>
                <p><strong>Purpose:</strong> Model validation and performance monitoring with live market data (paper trading)</p>
                <p><strong>Bot:</strong> Mansa_Bot (staging_bot.py) on Alpaca paper account</p>
              </div>
              
              <div class="card">
                <h3>🎯 What's Happening</h3>
                <ul>
                  <li>✅ Database migrations applied to staging environment</li>
                  <li>📈 Real market data ingestion active</li>
                  <li>🤖 Trading signals generated (paper trades only)</li>
                  <li>📊 Performance metrics logged to bot_performance_metrics</li>
                  <li>🧠 ML models training on live data patterns</li>
                </ul>
              </div>
              
              <div class="card">
                <h3>📅 Next Steps</h3>
                <ol>
                  <li><strong>Days 1-3:</strong> Monitor signal generation and data quality</li>
                  <li><strong>Week 1:</strong> Analyze bot_decision_audit for edge cases</li>
                  <li><strong>Week 2:</strong> Validate P&L calculations and Sharpe ratio</li>
                  <li><strong>Day 14:</strong> Review performance → Production deployment decision</li>
                </ol>
              </div>
              
              <div class="card">
                <h3>🔗 Resources</h3>
                <p><strong>Staging Bot:</strong> bbbot1_pipeline/staging_bot.py</p>
                <p><strong>Database:</strong> bbbot1 (port 3307)</p>
                <p><strong>Monitoring:</strong> Query bot_performance_metrics daily</p>
              </div>
            </div>
            <div class="footer">
              <p>Bentley Budget Bot | Staging Environment | Commit: ${commit}</p>
              <p>This is an automated message from GitHub Actions</p>
            </div>
          </body>
        </html>
      `;
    } else if (event === 'staging_migration_failed') {
      subject = '❌ Bentley Bot - Staging Migration Failed';
      body = `
        <html>
          <head>
            <style>
              body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
              .header { background: #ef4444; color: white; padding: 20px; text-align: center; }
              .content { padding: 20px; background: #f4f4f4; }
              .card { background: white; padding: 20px; margin: 10px 0; border-left: 4px solid #ef4444; }
              .error { color: #ef4444; font-weight: bold; }
            </style>
          </head>
          <body>
            <div class="header">
              <h1>❌ Staging Migration Failed</h1>
            </div>
            <div class="content">
              <div class="card">
                <h2 class="error">Migration Error Detected</h2>
                <p><strong>Status:</strong> ${message}</p>
                <p><strong>Branch:</strong> ${branch}</p>
                <p><strong>Commit:</strong> <code>${commit}</code></p>
              </div>
              
              <div class="card">
                <h3>⚠️ Impact</h3>
                <p>ML training phase cannot begin until migration is resolved.</p>
                <p><strong>Action Required:</strong> Check GitHub Actions logs immediately.</p>
              </div>
            </div>
            <div class="footer">
              <p>Bentley Budget Bot | Staging Environment | Commit: ${commit}</p>
            </div>
          </body>
        </html>
      `;
    }

    // Send email via Gmail
    const mailOptions = {
      from: `"Bentley Bot System" <${process.env.GMAIL_USER}>`,
      to: recipient,
      subject: subject,
      html: body
    };

    const info = await transporter.sendMail(mailOptions);
    log(`Email sent successfully: ${info.messageId}`);

    return res.json({
      success: true,
      event: event,
      status: status,
      emailId: info.messageId,
      recipient: recipient
    });

  } catch (err) {
    error(`Failed to send staging alert: ${err.message}`);
    return res.json({
      success: false,
      error: err.message
    }, 500);
  }
};
