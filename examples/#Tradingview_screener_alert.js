// Tradingview_screener_alert.js
// Node.js service — posts combined alerts (top gainers/losers + per-bot universe moves >=5%)
// to the Discord #general channel via DISCORD_BOT_TALK_WEBHOOK for all 15 Bentley Bots.

require('dotenv').config();
const axios = require('axios');
const cron = require('node-cron');

// Webhook resolution: DISCORD_BOT_TALK_WEBHOOK -> DISCORD_WEBHOOK_URL -> DISCORD_WEBHOOK
const DISCORD_WEBHOOK = (
  process.env.DISCORD_BOT_TALK_WEBHOOK ||
  process.env.DISCORD_WEBHOOK_URL ||
  process.env.DISCORD_WEBHOOK ||
  process.env.DISCORD_WEBHOOK_PROD ||
  ''
).trim();

// --- Bot Universe Definitions (sourced from bentley-bot/config/*.csv) -----------
const BOT_UNIVERSES = {
  'Titan'    : { fund: 'Mansa Tech',             universe: 'Mag7+Tech',                     tickers: ['AAPL','MSFT','NVDA','AVGO','AMD','AMZN','GOOGL','META'] },
  'Vega'     : { fund: 'Mansa Retail',            universe: 'Retail_Breakouts',              tickers: ['WMT','COST','TGT','TJX','ROST','BURL','ULTA','ANF'] },
  'Draco'    : { fund: 'Mansa Money Bag',         universe: 'Sentiment_Leaders',             tickers: ['KLAR','HOOD','AFFM','COIN','OPFI','JPM','BAC'] },
  'Altair'   : { fund: 'Mansa AI Fund',           universe: 'AI_News_Momentum',              tickers: ['QBTS','RGTI','QSI','QS','SOUN','NBIS','IONQ'] },
  'Procryon' : { fund: 'Prop Trading Fund',       universe: 'MT5_FX_CFD_Crypto_CFD',        tickers: ['COIN','MSTR','MARA','RIOT','CLSK','IREN','CIFR','HUT'] },
  'Hydra'    : { fund: 'Mansa Health',            universe: 'Healthcare_Momentum',           tickers: ['LLY','ABBV','BSX','ISRG','VRTX','DXCM','HCA','GILD'] },
  'Triton'   : { fund: 'Mansa Transportation',    universe: 'Transportation_Watchlist',      tickers: ['UBER','FDX','UPS','UNP','CSX','NSC','JBHT','DAL'] },
  'Dione'    : { fund: 'Mansa Options',           universe: 'Options_Mispricing',            tickers: ['SPY','QQQ','IWM','TSLA','NVDA','AAPL','AMZN','META'] },
  'Dogon'    : { fund: 'Mansa ETF',               universe: 'Core_ETF_Basket',               tickers: ['SPY','VTI','QQQ','DIA','IWM','XLK','XLF','XLV'] },
  'Rigel'    : { fund: 'Mansa FOREX',             universe: 'Forex_Macro',                   tickers: ['UUP','FXE','FXY','FXB','FXA','FXC','CYB','BZF'] },
  'Orion'    : { fund: 'Mansa Minerals',          universe: 'Minerals_Commodities',          tickers: ['GLD','GDX','NEM','FCX','SCCO','TECK','AA','RIO'] },
  'Rhea'     : { fund: 'Mansa ADI',               universe: 'Aerospace_Defense_Industrials', tickers: ['SIDU','AXON','NNE','GD','NOC','KTOS','HON','FLY','IR','XTIA'] },
  'Jupicita' : { fund: 'Mansa Smalls',            universe: 'Small_Cap_Pairs',               tickers: ['SOFI','HOOD','UPST','AFRM','IONQ','QBTS','RUN','ARRY'] },
  'Cephei'   : { fund: 'Mansa Functions Options', universe: 'Options_CFD',                   tickers: ['SPY','QQQ','IWM','AAPL','TSLA','NVDA','AMZN','META'] },
  'Cygnus'   : { fund: 'Mansa Shorts Fund',       universe: 'Pairs_Relative_Value',          tickers: ['XLF','XLK','XLE','SMH','XLI','IWM'] },
};

// All unique tickers across every bot -- used for top-gainers/losers scan
const ALL_TICKERS = [...new Set(Object.values(BOT_UNIVERSES).flatMap(b => b.tickers))];

// --- Yahoo Finance batched quote helper ------------------------------------------
async function fetchQuotes(symbols) {
  const results = {};
  const chunkSize = 20;
  for (let i = 0; i < symbols.length; i += chunkSize) {
    const chunk = symbols.slice(i, i + chunkSize);
    try {
      const url = `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${encodeURIComponent(chunk.join(','))}`;
      const { data } = await axios.get(url, { timeout: 12000 });
      for (const q of (data.quoteResponse?.result || [])) {
        results[q.symbol] = {
          symbol: q.symbol,
          price: q.regularMarketPrice,
          changePercent: q.regularMarketChangePercent,
          currency: q.currency || 'USD',
        };
      }
    } catch (err) {
      console.error(`Quote batch error [${chunk.join(',')}]:`, err.message);
    }
  }
  return results;
}

// --- Formatting helper ----------------------------------------------------------
const fmt = q => `\`${q.symbol}\` ${q.changePercent >= 0 ? '+' : ''}${q.changePercent.toFixed(2)}% | $${q.price.toFixed(2)}`;

// --- Discord posting (handles >10 embed limit by splitting) --------------------
async function postToDiscord(content, embeds = []) {
  if (!DISCORD_WEBHOOK) {
    console.warn('Discord webhook not configured -- set DISCORD_BOT_TALK_WEBHOOK');
    return;
  }
  const chunks = [];
  for (let i = 0; i < embeds.length; i += 10) chunks.push(embeds.slice(i, i + 10));
  for (const chunk of chunks) {
    try {
      await axios.post(DISCORD_WEBHOOK, { content, embeds: chunk });
      console.log(`Posted ${chunk.length} embed(s) to Discord.`);
    } catch (err) {
      console.error('Discord post error:', err.message);
    }
  }
}

// --- Main combined alert -------------------------------------------------------
async function runCombinedAlert() {
  console.log(`[${new Date().toISOString()}] Running combined alert for all 15 bots...`);

  // Single batched fetch for all tickers across all bot universes
  const quotes = await fetchQuotes(ALL_TICKERS);

  // Top Gainers & Losers across the full combined universe
  const allQuotes = Object.values(quotes).filter(q => q.changePercent != null);
  const gainers = [...allQuotes].sort((a, b) => b.changePercent - a.changePercent).slice(0, 5);
  const losers  = [...allQuotes].sort((a, b) => a.changePercent - b.changePercent).slice(0, 5);

  const embeds = [
    {
      title: '🚀 Top Gainers — All Bot Universes',
      description: gainers.length ? gainers.map(fmt).join('\n') : 'No data',
      color: 3066993,  // green
    },
    {
      title: '🔻 Top Losers — All Bot Universes',
      description: losers.length ? losers.map(fmt).join('\n') : 'No data',
      color: 15158332, // red
    },
  ];

  // Per-bot universe moves >= 5%
  for (const [botName, botInfo] of Object.entries(BOT_UNIVERSES)) {
    const moves = botInfo.tickers
      .map(t => quotes[t])
      .filter(q => q && Math.abs(q.changePercent) >= 5)
      .sort((a, b) => Math.abs(b.changePercent) - Math.abs(a.changePercent));

    embeds.push({
      title: `🤖 ${botName} (${botInfo.fund}) — ${botInfo.universe}`,
      description: moves.length
        ? moves.map(q => `${fmt(q)} ${q.changePercent >= 5 ? '🔥' : '⚠️'}`).join('\n')
        : '✅ No holdings moved >= 5%',
      color: moves.length ? 15105570 : 5592575, // orange if alerts, teal if quiet
      footer: { text: `Universe: ${botInfo.tickers.join(', ')}` },
    });
  }

  await postToDiscord('📊 **Bentley Bot — Daily Market & Universe Alerts**', embeds);
}

// --- Schedule: weekdays 9:30, 12:00, 15:30 ET ----------------------------------
cron.schedule('30 9 * * 1-5',  runCombinedAlert, { timezone: 'America/New_York' }); // 9:30 ET
cron.schedule('0 12 * * 1-5',  runCombinedAlert, { timezone: 'America/New_York' }); // 12:00 ET
cron.schedule('30 15 * * 1-5', runCombinedAlert, { timezone: 'America/New_York' }); // 15:30 ET

console.log('Bot_Talk screener alert service started. Scheduled for 9:30, 12:00, 15:30 ET weekdays.');

// Manual run for testing:
if (require.main === module) {
  runCombinedAlert();
}
