// index.js
require('dotenv').config();
const axios = require('axios');
const cron = require('node-cron');
const fs = require('fs');
const mysql = require('mysql2/promise');
const path = require('path');
const yaml = require('js-yaml');

const DISCORD_WEBHOOK = process.env.DISCORD_WEBHOOK;
const TIINGO_API_KEY = process.env.TIINGO_API_KEY || process.env.TIINGO_TOKEN;
const ALPHA_VANTAGE_API_KEY = process.env.ALPHA_VANTAGE_API_KEY || process.env.ALPHAVANTAGE_API_KEY;
const RUN_ONCE = process.argv.includes('--run-once');
const DEFAULT_MANSA_TECH_SYMBOLS = ['IONQ', 'QBTS', 'SOUN', 'RGTI', 'AMZN', 'NVDA'];
const ALERT_BOT = process.env.ALERT_BOT || process.env.BOT_NAME || 'Titan_Bot';
const ENFORCE_BOT_UNIVERSE = !['0', 'false', 'no', 'off'].includes(
  String(process.env.ENFORCE_BOT_UNIVERSE || 'true').trim().toLowerCase()
);
const BOT_CONFIG_DIR = path.resolve(__dirname, '..', 'bentley-bot', 'config', 'bots');
const BOT_DATA_DIR = path.resolve(__dirname, '..', 'bentley-bot', 'config');
const argShardIndex = process.argv.find(a => a.startsWith('--shard-index='));
const SHARD_INDEX_OVERRIDE = argShardIndex ? Number(argShardIndex.split('=')[1]) : null;
const SHARD_COUNT = Math.max(1, Number.parseInt(process.env.PORTFOLIO_SHARD_COUNT || '4', 10) || 4);
const SHARD_INDEX_ENV = Number.parseInt(process.env.PORTFOLIO_SHARD_INDEX || '', 10);
const MAX_SYMBOLS_PER_RUN = Number.parseInt(
  process.env.PORTFOLIO_MAX_SYMBOLS_PER_RUN || (ALPHA_VANTAGE_API_KEY ? '5' : '0'),
  10
);
let tiingoAccessChecked = false;
let tiingoAccessAvailable = false;
let alphaVantageRateLimited = false;
const botUniverseCache = new Map();

function normalizeTradingViewSymbol(value) {
  const token = String(value || '').trim().toUpperCase();
  if (!token) {
    return null;
  }

  if (!token.includes(':')) {
    return token;
  }

  const [exchange, symbol] = token.split(':', 2);
  if (!symbol) {
    return null;
  }

  if (exchange === 'TSX') {
    return `${symbol}.TO`;
  }

  if (exchange === 'TSXV') {
    return `${symbol}.V`;
  }

  return symbol;
}

function getBotSlug(botName) {
  const normalized = String(botName || '').trim().toLowerCase();
  if (normalized.endsWith('_bot')) {
    return normalized.slice(0, -4).replace(/\s+/g, '_');
  }
  return normalized.replace(/\s+/g, '_');
}

function loadBotUniverseContext(botName = ALERT_BOT) {
  const cacheKey = `${botName}`;
  if (botUniverseCache.has(cacheKey)) {
    return botUniverseCache.get(cacheKey);
  }

  try {
    const profilePath = path.join(BOT_CONFIG_DIR, `${getBotSlug(botName)}.yml`);
    const yamlText = fs.readFileSync(profilePath, 'utf8');
    const profile = yaml.load(yamlText) || {};
    const botMeta = typeof profile.bot === 'object' && profile.bot ? profile.bot : {};
    const strategyMeta = typeof profile.strategy === 'object' && profile.strategy ? profile.strategy : {};
    const runtimeName = String(botMeta.runtime_name || botMeta.name || botName || 'Unknown');
    const screenerFile = String(strategyMeta.screener_file || '').trim();
    const universe = String(strategyMeta.universe || '').trim();
    const screenerPath = path.join(BOT_DATA_DIR, screenerFile);

    let allowedSymbols = new Set();
    if (screenerFile && fs.existsSync(screenerPath)) {
      const csvText = fs.readFileSync(screenerPath, 'utf8').trim();
      const lines = csvText ? csvText.split(/\r?\n/) : [];
      if (lines.length > 0) {
        const headers = lines[0].split(',').map(h => h.trim());
        const symbolIndex = headers.findIndex(h => ['Ticker', 'Symbol', 'ticker', 'symbol'].includes(h));
        if (symbolIndex >= 0) {
          allowedSymbols = new Set(
            lines
              .slice(1)
              .map(line => line.split(',')[symbolIndex])
              .map(normalizeTradingViewSymbol)
              .filter(Boolean)
          );
        }
      }
    }

    const context = {
      loaded: true,
      botName: runtimeName,
      requestedBot: botName,
      universe,
      screenerFile,
      screenerPath,
      allowedSymbols
    };
    botUniverseCache.set(cacheKey, context);
    return context;
  } catch (err) {
    const context = {
      loaded: false,
      botName,
      requestedBot: botName,
      universe: '',
      screenerFile: '',
      screenerPath: '',
      allowedSymbols: new Set(),
      reason: err.message
    };
    botUniverseCache.set(cacheKey, context);
    return context;
  }
}

function filterSymbolsByBotUniverse(symbols, universeContext, sourceLabel) {
  if (!ENFORCE_BOT_UNIVERSE) {
    return Array.isArray(symbols) ? symbols : [];
  }

  if (!Array.isArray(symbols) || symbols.length === 0) {
    return [];
  }

  const filtered = symbols
    .map(normalizeTradingViewSymbol)
    .filter(symbol => symbol && universeContext.allowedSymbols.has(symbol));
  const unique = [...new Set(filtered)];

  console.log(
    `✓ Universe filter (${sourceLabel}) kept ${unique.length}/${symbols.length} ` +
    `symbols for ${universeContext.botName || ALERT_BOT}`
  );
  return unique;
}

function filterQuotesByBotUniverse(quotes, universeContext, sourceLabel) {
  if (!ENFORCE_BOT_UNIVERSE) {
    return Array.isArray(quotes) ? quotes : [];
  }

  if (!Array.isArray(quotes) || quotes.length === 0) {
    return [];
  }

  const filtered = quotes.filter((quote) => {
    const normalized = normalizeTradingViewSymbol(quote?.symbol);
    return normalized && universeContext.allowedSymbols.has(normalized);
  });

  console.log(
    `✓ Universe filter (${sourceLabel}) kept ${filtered.length}/${quotes.length} ` +
    `quotes for ${universeContext.botName || ALERT_BOT}`
  );
  return filtered;
}

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

function parseSymbols(raw) {
  if (!raw || typeof raw !== 'string') {
    return [];
  }

  return [...new Set(
    raw
      .split(',')
      .map(normalizeTradingViewSymbol)
      .filter(Boolean)
  )];
}

async function loadPortfolioSymbolsFromDb() {
  const userId = process.env.PORTFOLIO_USER_ID || process.env.MANSA_PORTFOLIO_USER_ID || 'demo_user';

  try {
    const pool = await getDbConnection();

    const [rows] = await pool.execute(
      `SELECT DISTINCT ticker
       FROM portfolios
       WHERE user_id = ?
       ORDER BY ticker`,
      [userId]
    );

    const symbols = rows
      .map(r => String(r.ticker || '').trim().toUpperCase())
      .filter(Boolean);

    if (symbols.length > 0) {
      console.log(`✓ Loaded ${symbols.length} portfolio symbols from DB for user ${userId}`);
    }

    return symbols;
  } catch (err) {
    console.warn(`Portfolio symbols DB lookup skipped: ${err.message}`);
    return [];
  }
}

async function resolvePortfolioSymbols() {
  const explicitSymbols = parseSymbols(process.env.PORTFOLIO_SYMBOLS || process.env.MANSA_TECH_SYMBOLS);
  if (explicitSymbols.length > 0) {
    console.log(`✓ Using explicit portfolio symbols from env (${explicitSymbols.length})`);
    return explicitSymbols;
  }

  const dbSymbols = await loadPortfolioSymbolsFromDb();
  if (dbSymbols.length > 0) {
    return dbSymbols;
  }

  console.log(`ℹ Using default Mansa Tech symbols (${DEFAULT_MANSA_TECH_SYMBOLS.length})`);
  return DEFAULT_MANSA_TECH_SYMBOLS;
}

function getAutoShardIndex() {
  const etHour = Number(
    new Intl.DateTimeFormat('en-US', {
      timeZone: 'America/New_York',
      hour: '2-digit',
      hour12: false
    }).format(new Date())
  );

  if (etHour < 8) return 0;
  if (etHour < 10) return 1;
  if (etHour < 12) return 2;
  return 3;
}

function selectPortfolioSymbolsForRun(symbols) {
  if (!Array.isArray(symbols) || symbols.length === 0) {
    return [];
  }

  const rawShardIndex = Number.isFinite(SHARD_INDEX_OVERRIDE)
    ? SHARD_INDEX_OVERRIDE
    : (Number.isFinite(SHARD_INDEX_ENV) ? SHARD_INDEX_ENV : getAutoShardIndex());
  const shardIndex = ((rawShardIndex % SHARD_COUNT) + SHARD_COUNT) % SHARD_COUNT;

  let selected = symbols.filter((_, idx) => idx % SHARD_COUNT === shardIndex);

  if (selected.length === 0) {
    selected = symbols;
  }

  if (Number.isFinite(MAX_SYMBOLS_PER_RUN) && MAX_SYMBOLS_PER_RUN > 0 && selected.length > MAX_SYMBOLS_PER_RUN) {
    selected = selected.slice(0, MAX_SYMBOLS_PER_RUN);
  }

  console.log(
    `✓ Portfolio selection: shard ${shardIndex + 1}/${SHARD_COUNT}, ` +
    `${selected.length}/${symbols.length} symbols this run`
  );

  return selected;
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

async function fetchQuoteFromTiingo(symbol) {
  if (!TIINGO_API_KEY) {
    return null;
  }

  if (!tiingoAccessChecked) {
    try {
      const resp = await axios.get('https://api.tiingo.com/api/test', {
        timeout: 8000,
        headers: { Authorization: `Token ${TIINGO_API_KEY}` }
      });
      tiingoAccessAvailable = resp.status === 200;
    } catch (err) {
      tiingoAccessAvailable = false;
      const status = err?.response?.status;
      if (status) {
        console.warn(`Tiingo preflight unavailable (HTTP ${status}); falling back to Yahoo quotes.`);
      } else {
        console.warn(`Tiingo preflight unavailable (${err.message}); falling back to Yahoo quotes.`);
      }
    } finally {
      tiingoAccessChecked = true;
    }
  }

  if (!tiingoAccessAvailable) {
    return null;
  }

  try {
    const end = new Date();
    const start = new Date(end);
    start.setDate(start.getDate() - 7);

    const toDateOnly = (d) => d.toISOString().slice(0, 10);

    const url = `https://api.tiingo.com/tiingo/daily/${encodeURIComponent(symbol)}/prices`;
    const { data } = await axios.get(url, {
      timeout: 10000,
      headers: {
        Authorization: `Token ${TIINGO_API_KEY}`
      },
      params: {
        startDate: toDateOnly(start),
        endDate: toDateOnly(end)
      }
    });

    if (!Array.isArray(data) || data.length === 0) {
      return null;
    }

    const latest = data[data.length - 1] || {};
    const latestClose = Number(latest.close ?? latest.adjClose);
    const previousClose = Number(
      latest.prevClose ?? (data.length > 1 ? data[data.length - 2]?.close : NaN)
    );

    const changePercent = Number.isFinite(previousClose) && previousClose !== 0
      ? ((latestClose - previousClose) / previousClose) * 100
      : null;

    if (!Number.isFinite(latestClose)) {
      return null;
    }

    return {
      symbol,
      price: latestClose,
      changePercent,
      currency: 'USD'
    };
  } catch (err) {
    const status = err?.response?.status;
    if (status === 401 || status === 403) {
      tiingoAccessAvailable = false;
      console.warn(`Tiingo quote access disabled (HTTP ${status}); using Yahoo fallback for remaining symbols.`);
    } else {
      console.warn(`Tiingo quote failed ${symbol}: ${err.message}`);
    }
    return null;
  }
}

async function fetchQuoteFromAlphaVantage(symbol) {
  if (!ALPHA_VANTAGE_API_KEY || alphaVantageRateLimited) {
    return null;
  }

  try {
    const url = 'https://www.alphavantage.co/query';
    const { data } = await axios.get(url, {
      timeout: 10000,
      params: {
        function: 'GLOBAL_QUOTE',
        symbol,
        apikey: ALPHA_VANTAGE_API_KEY
      }
    });

    if (data?.Note || data?.Information) {
      alphaVantageRateLimited = true;
      console.warn('AlphaVantage rate limit reached; using Yahoo fallback for remaining symbols.');
      return null;
    }

    const quote = data?.['Global Quote'];
    if (!quote || Object.keys(quote).length === 0) {
      return null;
    }

    const price = Number(quote['05. price']);
    const previousClose = Number(quote['08. previous close']);
    const rawChangePct = String(quote['10. change percent'] || '').replace('%', '').trim();
    const parsedChangePct = Number(rawChangePct);
    const changePercent = Number.isFinite(parsedChangePct)
      ? parsedChangePct
      : (Number.isFinite(previousClose) && previousClose !== 0 && Number.isFinite(price)
        ? ((price - previousClose) / previousClose) * 100
        : null);

    if (!Number.isFinite(price)) {
      return null;
    }

    return {
      symbol,
      price,
      changePercent,
      currency: 'USD'
    };
  } catch (err) {
    console.warn(`AlphaVantage quote failed ${symbol}: ${err.message}`);
    return null;
  }
}

// Simple Yahoo Finance quote fetch
async function fetchQuoteFromYahoo(symbol) {
  try {
    const url = `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${encodeURIComponent(symbol)}`;
    const { data } = await axios.get(url, {
      timeout: 10000,
      headers: { 'User-Agent': 'Mozilla/5.0' }
    });
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

async function fetchQuote(symbol) {
  const tiingoQuote = await fetchQuoteFromTiingo(symbol);
  if (tiingoQuote) {
    return tiingoQuote;
  }

  const alphaVantageQuote = await fetchQuoteFromAlphaVantage(symbol);
  if (alphaVantageQuote) {
    return alphaVantageQuote;
  }

  return fetchQuoteFromYahoo(symbol);
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

// ---------- Universe-based gainers/losers (ranked from bot universe quotes) ----------
async function fetchUniverseGainersLosers(symbols, gainLimit = 5, lossLimit = 5) {
  const results = await Promise.all(symbols.map(s => fetchQuote(s)));
  const valid = results.filter(q => q && Number.isFinite(Number(q.changePercent)));
  if (valid.length === 0) {
    return { gainers: [], losers: [] };
  }
  valid.sort((a, b) => Number(b.changePercent) - Number(a.changePercent));
  const gainers = valid.slice(0, gainLimit);
  const losers = valid.slice(-lossLimit).reverse();
  return { gainers, losers };
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
  if (!DISCORD_WEBHOOK) {
    const message = 'DISCORD_WEBHOOK is not configured';
    console.error(message);
    return message;
  }

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
  try {
    const universeContext = loadBotUniverseContext(ALERT_BOT);
    if (ENFORCE_BOT_UNIVERSE && (!universeContext.loaded || universeContext.allowedSymbols.size === 0)) {
      console.warn(
        `Universe enforcement blocked alerts for ${ALERT_BOT}: ` +
        `${universeContext.reason || 'configured universe is empty'}`
      );
      return;
    }

    const portfolioAll = await resolvePortfolioSymbols();
    const universePortfolio = filterSymbolsByBotUniverse(
      portfolioAll,
      universeContext,
      'portfolio source'
    );
    const portfolio = selectPortfolioSymbolsForRun(universePortfolio);
    const universeSymbols = universeContext.allowedSymbols.size > 0
      ? Array.from(universeContext.allowedSymbols)
      : [];

    let gainers, losers;
    if (universeSymbols.length > 0) {
      // Fetch and rank quotes directly from the bot universe (avoids empty filter on global screener)
      const g = await fetchUniverseGainersLosers(universeSymbols, 5, 5);
      gainers = g.gainers;
      losers = g.losers;
      console.log(`✓ Universe gainers/losers: ${gainers.length} gainers, ${losers.length} losers from ${universeSymbols.length} symbols`);
    } else {
      // Fallback to global Yahoo screener + universe filter
      const [gainersRaw, losersRaw] = await Promise.all([fetchTopGainers(5), fetchTopLosers(5)]);
      gainers = filterQuotesByBotUniverse(gainersRaw, universeContext, 'top gainers');
      losers = filterQuotesByBotUniverse(losersRaw, universeContext, 'top losers');
    }

    const portfolioMovesRaw = await portfolioAlerts(portfolio, 5);
    const portfolioMoves = filterQuotesByBotUniverse(
      portfolioMovesRaw,
      universeContext,
      'portfolio moves'
    );

    const fmt = q => {
      const symbol = q?.symbol || 'N/A';
      const rawChange = Number(q?.changePercent);
      const rawPrice = Number(q?.price);
      const change = Number.isFinite(rawChange) ? rawChange.toFixed(2) : 'N/A';
      const price = Number.isFinite(rawPrice) ? rawPrice : 'N/A';
      const currency = q?.currency || 'USD';
      return `${symbol} ${change}% | ${currency} ${price}`;
    };

    const universeLabel = universeContext.universe || 'Configured Universe';
    const content = `${universeContext.botName || ALERT_BOT} | ${universeLabel} Alerts`;
    const embeds = [
      {
        title: `Top Gainers | ${universeLabel}`,
        description:
          gainers.length
            ? gainers.map(fmt).join('\n')
            : 'No data',
        color: 3066993 // green
      },
      {
        title: `Top Losers | ${universeLabel}`,
        description:
          losers.length
            ? losers.map(fmt).join('\n')
            : 'No data',
        color: 15158332 // red
      },
      {
        title: `Portfolio Moves ≥ 5% | ${universeLabel}`,
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
        Number.isFinite(Number(alert.changePercent)) ? Number(alert.changePercent) : null,
        Number.isFinite(Number(alert.price)) ? Number(alert.price) : null,
        alert.currency || 'USD',
        alert.type,
        delivered,
        error
      );
    }

    console.log(`Logged ${allAlerts.length} alerts to database`);
  } catch (err) {
    console.error('runCombinedAlert failed:', err.message);
  }
}

// ---------- Schedule (Cron format: minute hour * * day-of-week) ----------
// Format: 'minute hour * * 1-5' for weekdays (1=Mon, 5=Fri), timezone: America/New_York

function startDaemonSchedule() {
  // 7:00 AM ET
  cron.schedule('0 7 * * 1-5', runCombinedAlert, { timezone: 'America/New_York' });

  // 9:40 AM ET
  cron.schedule('40 9 * * 1-5', runCombinedAlert, { timezone: 'America/New_York' });

  // 11:30 AM ET
  cron.schedule('30 11 * * 1-5', runCombinedAlert, { timezone: 'America/New_York' });

  // 3:00 PM ET
  cron.schedule('0 15 * * 1-5', runCombinedAlert, { timezone: 'America/New_York' });
}

// Manual run for testing:
if (require.main === module) {
  if (RUN_ONCE) {
    console.log('🚀 Running one-shot Daily Market & Portfolio Alert...');
    runCombinedAlert().finally(async () => {
      if (dbPool) {
        await dbPool.end();
      }
      process.exit(0);
    });
  } else {
    console.log('🚀 Starting TradingView Alerts Service...');
    console.log('📅 Scheduled for: 7:00 AM, 9:40 AM, 11:30 AM, 3:00 PM ET (weekdays)');
    console.log(`🧭 Alert bot universe: ${ALERT_BOT} | enforce=${ENFORCE_BOT_UNIVERSE}`);
    startDaemonSchedule();
    runCombinedAlert();
  }
}
