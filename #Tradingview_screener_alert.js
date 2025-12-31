#Tradingview_screener_alert
# This script listens for TradingView webhook alerts and processes them.
# It extracts relevant information from the alert payload and prints it to the console.
#Node.js service that posts combined alerts (top gainers/losers + your portfolio moves >5%) to a Discord channel via a webhook. 

// index.js
require('dotenv').config();
const axios = require('axios');
const cron = require('node-cron');

const DISCORD_WEBHOOK = process.env.DISCORD_WEBHOOK;

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

// Example “gainers/losers” via Yahoo Finance screener endpoints or your provider.
// Replace stubs with your authenticated API if needed.
async function fetchTopGainers(limit = 5) {
  try {
    // Placeholder: Replace with your provider’s gainers endpoint
    // For demo, pick a static list then sort by daily change.
    const symbols = ['AAPL', 'MSFT', 'TSLA', 'NVDA', 'AMD', 'META', 'AMZN'];
    const quotes = await Promise.all(symbols.map(fetchQuote));
    return quotes
      .filter(q => q)
      .sort((a, b) => b.changePercent - a.changePercent)
      .slice(0, limit);
  } catch (err) {
    console.error('Gainers error:', err.message);
    return [];
  }
}

async function fetchTopLosers(limit = 5) {
  try {
    const symbols = ['AAPL', 'MSFT', 'TSLA', 'NVDA', 'AMD', 'META', 'AMZN'];
    const quotes = await Promise.all(symbols.map(fetchQuote));
    return quotes
      .filter(q => q)
      .sort((a, b) => a.changePercent - b.changePercent)
      .slice(0, limit);
  } catch (err) {
    console.error('Losers error:', err.message);
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
  } catch (err) {
    console.error('Discord post error:', err.message);
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

  await postToDiscord(content, embeds);
}

// ---------- Schedule (e.g., weekdays 9:30, 12:00, 15:30 ET) ----------
cron.schedule('30 14 * * 1-5', runCombinedAlert, { timezone: 'America/New_York' }); // 9:30 ET
cron.schedule('0 17 * * 1-5', runCombinedAlert, { timezone: 'America/New_York' });  // 12:00 ET
cron.schedule('30 20 * * 1-5', runCombinedAlert, { timezone: 'America/New_York' }); // 15:30 ET

// Manual run for testing:
if (require.main === module) {
  runCombinedAlert();
}


