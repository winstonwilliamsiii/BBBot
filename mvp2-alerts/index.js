// index.js
require('dotenv').config();
const axios = require('axios');
const cron = require('node-cron');
const mysql = require('mysql2/promise');

const DISCORD_WEBHOOK = process.env.DISCORD_WEBHOOK;

// ---------- MySQL Connection (Railway Cloud or Local) ----------
let dbPool;

// Support both individual variables AND MySQL URL
const dbConfig = process.env.MYSQL_URL 
  ? {} // Let mysql2 parse the URL
  : {
      host: process.env.MYSQL_HOST || '127.0.0.1',
      port: parseInt(process.env.MYSQL_PORT || '3306'),
      user: process.env.MYSQL_USER || 'root',
      password: process.env.MYSQL_PASSWORD || 'root',
      database: process.env.MYSQL_DATABASE || 'bbbot1',
      waitForConnections: true,
      connectionLimit: 10,
      queueLimit: 0
    };

async function getDbConnection() {
  if (!dbPool) {
    if (process.env.MYSQL_URL) {
      // Railway style: mysql://user:password@host:port/database
      dbPool = mysql.createPool(process.env.MYSQL_URL);
      console.log('✓ Connected to Railway MySQL');
    } else {
      // Local or env variables style
      dbPool = mysql.createPool(dbConfig);
      console.log('✓ Connected to local MySQL');
    }
  }
  return dbPool;
}

// ---------- Alert Logging ----------
async function logAlert(symbol, changePercent, price, currency, alertType, discordDelivered, discordError = null) {
  try {
    const pool = await getDbConnection();
    await pool.execute(
      `INSERT INTO alerts_log (symbol, change_percent, price, currency, alert_type, discord_delivered, discord_error) 
       VALUES (?, ?, ?, ?, ?, ?, ?)`,
      [symbol, changePercent, price, currency, alertType, discordDelivered, discordError]
    );
    console.log(`✓ Logged alert: ${symbol} ${alertType}`);
  } catch (err) {
    console.error('MySQL log error:', err.message);
  }
}

// ---------- Data sources (replace with your preferred APIs) ----------

// Simple Yahoo Finance quote fetch
async function fetchQuote(symbol) {
  try {
    const url = `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${encodeURIComponent(symbol)}`;
    const { data } = await axios.get(url, { timeout: 10000 });
    const q = data.quoteResponse.result[0];
    if (!q) return null;
    return {
      symbol: q.symbol,
      price: q.regularMarketPrice,
      changePercent: q.regularMarketChangePercent,
      currency: q.currency
    };
  } catch (err) {
    console.error(`Quote error ${symbol}:`, err.message);
    return null;
  }
}

// Yahoo Finance screener endpoints for top gainers/losers
async function fetchTopGainers(limit = 5) {
  try {
    const url = 'https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?scrIds=day_gainers&count=25';
    const { data } = await axios.get(url, { 
      timeout: 10000,
      headers: { 'User-Agent': 'Mozilla/5.0' }
    });
    
    const quotes = data.finance.result[0].quotes || [];
    return quotes.slice(0, limit).map(q => ({
      symbol: q.symbol,
      price: q.regularMarketPrice,
      changePercent: q.regularMarketChangePercent,
      currency: q.currency || 'USD'
    }));
  } catch (err) {
    console.error('Gainers error:', err.message);
    // Fallback to empty array
    return [];
  }
}

async function fetchTopLosers(limit = 5) {
  try {
    const url = 'https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?scrIds=day_losers&count=25';
    const { data } = await axios.get(url, { 
      timeout: 10000,
      headers: { 'User-Agent': 'Mozilla/5.0' }
    });
    
    const quotes = data.finance.result[0].quotes || [];
    return quotes.slice(0, limit).map(q => ({
      symbol: q.symbol,
      price: q.regularMarketPrice,
      changePercent: q.regularMarketChangePercent,
      currency: q.currency || 'USD'
    }));
  } catch (err) {
    console.error('Losers error:', err.message);
    // Fallback to empty array
    return [];
  }
}

// ---------- Portfolio alerts (>5% move) ----------
async function portfolioAlerts(portfolioSymbols, thresholdPct = 5) {
  const alerts = [];
  for (const s of portfolioSymbols) {
    const q = await fetchQuote(s);
    if (q && Math.abs(q.changePercent) >= thresholdPct) {
      alerts.push(q);
    }
  }
  return alerts;
}

// ---------- Discord posting ----------
async function postToDiscord(content, embeds = []) {
  try {
    await axios.post(DISCORD_WEBHOOK, { content, embeds });
    console.log('Posted to Discord.');
    return true;
  } catch (err) {
    console.error('Discord post error:', err.message);
    return err.message;
  }
}

// ---------- Compose and send combined alert ----------
async function runCombinedAlert() {
  const portfolio = ['AAPL', 'MSFT', 'TSLA']; // replace with your holdings
  const [gainers, losers, portfolioMoves] = await Promise.all([
    fetchTopGainers(5),
    fetchTopLosers(5),
    portfolioAlerts(portfolio, 5)
  ]);

  const fmt = q =>
    `${q.symbol} ${q.changePercent.toFixed(2)}% | ${q.currency} ${q.price}`;

  const content = 'Daily Market & Portfolio Alerts';
  const embeds = [
    {
      title: 'Top Gainers',
      description:
        gainers.length
          ? gainers.map(fmt).join('\n')
          : 'No data',
      color: 3066993 // green
    },
    {
      title: 'Top Losers',
      description:
        losers.length
          ? losers.map(fmt).join('\n')
          : 'No data',
      color: 15158332 // red
    },
    {
      title: 'Portfolio Moves ≥ 5%',
      description:
        portfolioMoves.length
          ? portfolioMoves.map(fmt).join('\n')
          : 'No holdings exceeded threshold',
      color: 3447003 // blue
    }
  ];

  // Send to Discord and get result
  const discordResult = await postToDiscord(content, embeds);
  const delivered = discordResult === true;
  const error = delivered ? null : discordResult;

  // Log all alerts to MySQL
  const allAlerts = [
    ...gainers.map(q => ({ ...q, type: 'gainer' })),
    ...losers.map(q => ({ ...q, type: 'loser' })),
    ...portfolioMoves.map(q => ({ ...q, type: 'portfolio' }))
  ];

  for (const alert of allAlerts) {
    await logAlert(
      alert.symbol,
      alert.changePercent,
      alert.price,
      alert.currency,
      alert.type,
      delivered,
      error
    );
  }

  console.log(`Logged ${allAlerts.length} alerts to database`);
}

// ---------- Schedule (Cron format: minute hour * * day-of-week) ----------
// Format: 'minute hour * * 1-5' for weekdays (1=Mon, 5=Fri), timezone: America/New_York

// 7:00 AM ET
cron.schedule('0 7 * * 1-5', runCombinedAlert, { timezone: 'America/New_York' });

// 9:40 AM ET
cron.schedule('40 9 * * 1-5', runCombinedAlert, { timezone: 'America/New_York' });

// 11:30 AM ET
cron.schedule('30 11 * * 1-5', runCombinedAlert, { timezone: 'America/New_York' });

// 3:00 PM ET
cron.schedule('0 15 * * 1-5', runCombinedAlert, { timezone: 'America/New_York' });

// Manual run for testing:
if (require.main === module) {
  console.log('🚀 Starting TradingView Alerts Service...');
  console.log('📅 Scheduled for: 7:00 AM, 9:40 AM, 11:30 AM, 3:00 PM ET (weekdays)');
  runCombinedAlert();
}
