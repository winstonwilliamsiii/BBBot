// index.js
const axios = require('axios');
const cron = require('node-cron');
const YahooFinanceLib = require('yahoo-finance2').default;
const yahooFinance = new YahooFinanceLib({ suppressNotices: ['yahooSurvey'] });
const fs = require('fs');
const mysql = require('mysql2/promise');
const path = require('path');
const yaml = require('js-yaml');
require('dotenv').config({ path: path.resolve(__dirname, '.env'), override: true });

const DISCORD_WEBHOOK =
  process.env.DISCORD_WEBHOOK ||
  process.env.DISCORD_BOT_TALK_WEBHOOK ||
  process.env.DISCORD_WEBHOOK_URL ||
  process.env.DISCORD_WEBHOOK_PROD;
const TIINGO_API_KEY = process.env.TIINGO_API_KEY || process.env.TIINGO_TOKEN;
const ALPHA_VANTAGE_API_KEY = process.env.ALPHA_VANTAGE_API_KEY || process.env.ALPHAVANTAGE_API_KEY;
const RUN_ONCE = process.argv.includes('--run-once');
const DEFAULT_MANSA_TECH_SYMBOLS = ['IONQ', 'QBTS', 'SOUN', 'RGTI', 'AMZN', 'NVDA'];
const ALERT_BOT = process.env.ALERT_BOT || process.env.BOT_NAME || 'Titan_Bot';
const ALERT_MODE = String(process.env.ALERT_MODE || 'daily').trim().toLowerCase();
const ALERT_SIGNALS_PER_BOT = Math.max(
  1,
  Number.parseInt(process.env.ALERT_SIGNALS_PER_BOT || '15', 10) || 15
);
const TITAN_RUNTIME_NAME = 'Titan_Bot';
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

function getSignalIndicator(changePercent) {
  const value = Number(changePercent);
  if (!Number.isFinite(value)) {
    return 'HOLD';
  }
  if (value > 0) {
    return 'BUY';
  }
  if (value < 0) {
    return 'SELL';
  }
  return 'HOLD';
}

function isRetryableDbError(err) {
  const code = String(err?.code || '').toUpperCase();
  const message = String(err?.message || '').toLowerCase();
  return (
    code === 'PROTOCOL_CONNECTION_LOST' ||
    code === 'ECONNRESET' ||
    code === 'ETIMEDOUT' ||
    code === 'PROTOCOL_ENQUEUE_AFTER_FATAL_ERROR' ||
    message.includes('connection lost') ||
    message.includes('server has gone away') ||
    message.includes('closed the connection')
  );
}

function normalizeBotRuntimeName(name) {
  const trimmed = String(name || '').trim();
  if (!trimmed) {
    return null;
  }
  return trimmed.endsWith('_Bot') ? trimmed : `${trimmed}_Bot`;
}

function resolveConfiguredAlertBots() {
  const explicit = String(process.env.ALERT_BOTS || '').trim();
  if (explicit) {
    return [...new Set(
      explicit
        .split(',')
        .map(normalizeBotRuntimeName)
        .filter(Boolean)
    )].sort((a, b) => a.localeCompare(b));
  }

  try {
    const files = fs.readdirSync(BOT_CONFIG_DIR).filter((fileName) => fileName.endsWith('.yml'));
    const runtimes = files
      .map((fileName) => {
        try {
          const profilePath = path.join(BOT_CONFIG_DIR, fileName);
          const yamlText = fs.readFileSync(profilePath, 'utf8');
          const profile = yaml.load(yamlText) || {};
          const botMeta = typeof profile.bot === 'object' && profile.bot ? profile.bot : {};
          return normalizeBotRuntimeName(botMeta.runtime_name || botMeta.name || '');
        } catch (err) {
          console.warn(`Failed to parse bot config ${fileName}: ${err.message}`);
          return null;
        }
      })
      .filter(Boolean);

    if (runtimes.length > 0) {
      return [...new Set(runtimes)].sort((a, b) => a.localeCompare(b));
    }
  } catch (err) {
    console.warn(`Failed to enumerate bot configs in ${BOT_CONFIG_DIR}: ${err.message}`);
  }

  return [normalizeBotRuntimeName(ALERT_BOT) || TITAN_RUNTIME_NAME].sort((a, b) => a.localeCompare(b));
}

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
      host: process.env.BBBOT1_MYSQL_HOST || process.env.MYSQL_HOST || '127.0.0.1',
      port: parseInt(process.env.BBBOT1_MYSQL_PORT || process.env.MYSQL_PORT || '3306', 10),
      user: process.env.BBBOT1_MYSQL_USER || process.env.MYSQL_USER || 'root',
      password: process.env.BBBOT1_MYSQL_PASSWORD || process.env.MYSQL_PASSWORD || 'root',
      database: process.env.BBBOT1_MYSQL_DATABASE || process.env.MYSQL_DATABASE || 'bbbot1',
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

async function resetDbConnection() {
  if (dbPool) {
    try {
      await dbPool.end();
    } catch (err) {
      // ignore close errors while resetting the pool
    }
  }
  dbPool = null;
  alertsLogInsertConfigPromise = null;
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
let alertsLogInsertConfigPromise = null;

async function getAlertsLogInsertConfig() {
  if (alertsLogInsertConfigPromise) {
    return alertsLogInsertConfigPromise;
  }

  alertsLogInsertConfigPromise = (async () => {
    const pool = await getDbConnection();

    // Ensure the logging table exists, then adapt inserts to the live schema.
    await pool.execute(`
      CREATE TABLE IF NOT EXISTS alerts_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        symbol VARCHAR(20) NOT NULL,
        change_percent DECIMAL(6,2) NOT NULL,
        price DECIMAL(12,2),
        currency VARCHAR(10) DEFAULT 'USD',
        alert_type VARCHAR(50) NOT NULL,
        discord_delivered BOOLEAN DEFAULT FALSE,
        discord_error TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_symbol (symbol),
        INDEX idx_sent_at (sent_at),
        INDEX idx_alert_type (alert_type)
      ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    `);

    const [rows] = await pool.query('SHOW COLUMNS FROM alerts_log');
    const normalizedRows = (rows || []).map((r) => ({
      name: String(r.Field || '').toLowerCase(),
      type: String(r.Type || '').toLowerCase(),
      nullable: String(r.Null || '').toUpperCase() === 'YES',
      hasDefault: r.Default !== null && r.Default !== undefined,
      extra: String(r.Extra || '').toLowerCase()
    }));
    const columns = new Set(normalizedRows.map((r) => r.name));

    const pick = (...candidates) => candidates.find((name) => columns.has(name)) || null;

    const mapped = {
      botName: pick('bot_name', 'bot', 'runtime_name'),
      symbol: pick('symbol', 'ticker'),
      changePercent: pick('change_percent', 'pct_change', 'percent_change', 'change_pct'),
      price: pick('price', 'last_price', 'market_price'),
      currency: pick('currency', 'ccy'),
      alertType: pick('alert_type', 'type', 'event_type'),
      message: pick('message', 'content', 'summary'),
      payload: pick('payload', 'payload_json', 'data'),
      channel: pick('channel', 'destination', 'target_channel'),
      status: pick('status', 'delivery_status'),
      discordDelivered: pick('discord_delivered', 'delivered', 'is_delivered'),
      discordError: pick('discord_error', 'error', 'error_message')
    };

    const insertColumns = [];
    const valueGetters = [];

    const add = (columnName, getter) => {
      if (!columnName) {
        return;
      }
      insertColumns.push(columnName);
      valueGetters.push(getter);
    };

    add(mapped.botName, (payload) => payload.botName);
    add(mapped.symbol, (payload) => payload.symbol);
    add(mapped.changePercent, (payload) => payload.changePercent);
    add(mapped.price, (payload) => payload.price);
    add(mapped.currency, (payload) => payload.currency);
    add(mapped.alertType, (payload) => payload.alertType);
    add(mapped.message, (payload) => payload.message);
    add(mapped.payload, (payload) => payload.payload);
    add(mapped.channel, (payload) => payload.channel);
    add(mapped.status, (payload) => payload.status);
    add(mapped.discordDelivered, (payload) => payload.discordDelivered);
    add(mapped.discordError, (payload) => payload.discordError);

    const inserted = new Set(insertColumns.map((name) => String(name).toLowerCase()));
    for (const column of normalizedRows) {
      if (inserted.has(column.name)) {
        continue;
      }
      if (column.extra.includes('auto_increment')) {
        continue;
      }
      if (column.nullable || column.hasDefault) {
        continue;
      }

      add(column.name, () => {
        if (column.type.includes('json')) {
          return '{}';
        }
        if (column.type.includes('int') || column.type.includes('decimal') || column.type.includes('float') || column.type.includes('double')) {
          return 0;
        }
        if (column.type.includes('date') || column.type.includes('time')) {
          return new Date();
        }
        return '';
      });
    }

    if (insertColumns.length === 0) {
      throw new Error('alerts_log has no compatible columns for alert logging');
    }

    const placeholders = insertColumns.map(() => '?').join(', ');
    const sql = `INSERT INTO alerts_log (${insertColumns.join(', ')}) VALUES (${placeholders})`;

    console.log(`✓ alerts_log schema detected; using columns: ${insertColumns.join(', ')}`);
    return { sql, valueGetters };
  })().catch((err) => {
    alertsLogInsertConfigPromise = null;
    throw err;
  });

  return alertsLogInsertConfigPromise;
}

async function logAlert(symbol, changePercent, price, currency, alertType, discordDelivered, discordError = null, botName = '', extra = {}, attempt = 1) {
  try {
    const pool = await getDbConnection();
    const insertConfig = await getAlertsLogInsertConfig();
    const normalizedSymbol = String(symbol || '').trim().toUpperCase();
    const normalizedType = String(alertType || 'signal').trim().toLowerCase();
    const normalizedBot = String(botName || ALERT_BOT || 'Unknown_Bot').trim();
    const signalIndicator = String(extra.signalIndicator || getSignalIndicator(changePercent));
    const alertGroup = String(extra.alertGroup || '').trim().toLowerCase();
    const message = `${normalizedBot} | ${normalizedType} | ${normalizedSymbol} ${Number.isFinite(Number(changePercent)) ? `${Number(changePercent).toFixed(2)}%` : 'N/A'} | ${signalIndicator}`;
    const payload = {
      botName: normalizedBot,
      symbol: normalizedSymbol,
      changePercent,
      price,
      currency,
      alertType: normalizedType,
      message,
      payload: JSON.stringify({
        bot_name: normalizedBot,
        symbol: normalizedSymbol,
        change_percent: changePercent,
        price,
        currency,
        alert_type: normalizedType,
        signal_indicator: signalIndicator,
        alert_group: alertGroup || (normalizedType === 'signal' ? 'all_bot_signals' : 'daily_market_portfolio'),
        discord_delivered: Boolean(discordDelivered),
        discord_error: discordError
      }),
      channel: 'discord',
      status: discordDelivered ? 'sent' : 'failed',
      discordDelivered,
      discordError
    };
    const values = insertConfig.valueGetters.map((getter) => getter(payload));

    await pool.execute(insertConfig.sql, values);
    console.log(`✓ Logged alert: ${symbol} ${alertType}`);
  } catch (err) {
    if (attempt < 2 && isRetryableDbError(err)) {
      console.warn(`MySQL log retry (${attempt}) after transient error: ${err.message}`);
      await resetDbConnection();
      return logAlert(symbol, changePercent, price, currency, alertType, discordDelivered, discordError, botName, extra, attempt + 1);
    }
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
    const q = await yahooFinance.quote(symbol, {}, { validateResult: false });
    if (!q) return null;
    return {
      symbol: q.symbol,
      price: q.regularMarketPrice,
      changePercent: q.regularMarketChangePercent,
      currency: q.currency || 'USD'
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

async function fetchUniverseSignals(symbols, signalLimit = ALERT_SIGNALS_PER_BOT) {
  const results = await Promise.all(symbols.map(s => fetchQuote(s)));
  const valid = results.filter(q => q && Number.isFinite(Number(q.changePercent)));
  if (valid.length === 0) {
    return [];
  }

  valid.sort((a, b) => Math.abs(Number(b.changePercent)) - Math.abs(Number(a.changePercent)));
  return valid.slice(0, signalLimit);
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

function formatQuote(q) {
  const symbol = q?.symbol || 'N/A';
  const rawChange = Number(q?.changePercent);
  const rawPrice = Number(q?.price);
  const change = Number.isFinite(rawChange) ? rawChange.toFixed(2) : 'N/A';
  const price = Number.isFinite(rawPrice) ? rawPrice : 'N/A';
  const currency = q?.currency || 'USD';
  return `${symbol} ${change}% | ${currency} ${price}`;
}

function formatSignalQuote(q) {
  const indicator = getSignalIndicator(q?.changePercent);
  return `${formatQuote(q)} | ${indicator}`;
}

async function collectBotMarketData(botName) {
  const universeContext = loadBotUniverseContext(botName);
  if (ENFORCE_BOT_UNIVERSE && (!universeContext.loaded || universeContext.allowedSymbols.size === 0)) {
    console.warn(
      `Universe enforcement blocked alerts for ${botName}: ` +
      `${universeContext.reason || 'configured universe is empty'}`
    );
    return null;
  }

  const universeSymbols = universeContext.allowedSymbols.size > 0
    ? Array.from(universeContext.allowedSymbols)
    : [];

  if (universeSymbols.length === 0) {
    console.warn(`No configured universe symbols found for ${botName}; skipping alert.`);
    return null;
  }

  let gainers, losers;
  const g = await fetchUniverseGainersLosers(universeSymbols, 5, 5);
  gainers = g.gainers;
  losers = g.losers;
  console.log(`✓ Universe gainers/losers: ${gainers.length} gainers, ${losers.length} losers from ${universeSymbols.length} symbols`);

  const universeSignals = await fetchUniverseSignals(universeSymbols, ALERT_SIGNALS_PER_BOT);
  const portfolioSource = selectPortfolioSymbolsForRun(universeSymbols);
  const portfolioMovesRaw = await portfolioAlerts(portfolioSource, 5);
  const portfolioMoves = filterQuotesByBotUniverse(
    portfolioMovesRaw,
    universeContext,
    'portfolio moves'
  );

  return {
    runtimeName: universeContext.botName || botName,
    universeLabel: universeContext.universe || 'Configured Universe',
    universeSignals,
    gainers,
    losers,
    portfolioMoves
  };
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
async function runAllBotSignalsForBot(botName) {
  try {
    const data = await collectBotMarketData(botName);
    if (!data) {
      return;
    }

    const content = `🤖 All Bot Signals | ${data.runtimeName} | ${data.universeLabel}`;
    const totalDataPoints = data.universeSignals.length;
    const dataQualityWarning = totalDataPoints === 0
      ? [{ title: '⚠️ Data Provider Warning', description: 'All market data sources failed (Tiingo 403, AlphaVantage DNS, Yahoo fallback). Quotes unavailable — check API keys and network.', color: 16776960 }]
      : [];
    const embeds = [...dataQualityWarning,
      {
        title: `All Bot Signals | ${data.universeLabel}`,
        description:
          data.universeSignals.length
            ? data.universeSignals.map(formatQuote).join('\n')
            : 'No universe signal data',
        color: 5592575 // teal
      }
    ];

    // Send to Discord and get result
    const discordResult = await postToDiscord(content, embeds);
    const delivered = discordResult === true;
    const error = delivered ? null : discordResult;

    // Log all alerts to MySQL
    const allAlerts = [
      ...data.universeSignals.map(q => ({ ...q, type: 'signal' }))
    ];

    for (const alert of allAlerts) {
      await logAlert(
        alert.symbol,
        Number.isFinite(Number(alert.changePercent)) ? Number(alert.changePercent) : null,
        Number.isFinite(Number(alert.price)) ? Number(alert.price) : null,
        alert.currency || 'USD',
        alert.type,
        delivered,
        error,
        data.runtimeName
      );
    }

    console.log(`Logged ${allAlerts.length} signal alerts to database for ${data.runtimeName}`);
  } catch (err) {
    console.error(`runAllBotSignalsForBot failed (${botName}):`, err.message);
  }
}

async function runDailyMarketAndPortfolioForBot(botName) {
  try {
    const data = await collectBotMarketData(botName);
    if (!data) {
      return;
    }

    const content = `📊 Daily Market and Portfolio | ${data.runtimeName} | ${data.universeLabel}`;
    const totalDataPoints = data.gainers.length + data.losers.length;
    const dataQualityWarning = totalDataPoints === 0
      ? [{ title: '⚠️ Data Provider Warning', description: 'All market data sources failed (Tiingo 403, AlphaVantage DNS, Yahoo fallback). Quotes unavailable — check API keys and network.', color: 16776960 }]
      : [];

    const embeds = [...dataQualityWarning,
      {
        title: `Top Gainers | ${data.universeLabel}`,
        description:
          data.gainers.length
            ? data.gainers.map(formatQuote).join('\n')
            : 'No data',
        color: 3066993 // green
      },
      {
        title: `Top Losers | ${data.universeLabel}`,
        description:
          data.losers.length
            ? data.losers.map(formatQuote).join('\n')
            : 'No data',
        color: 15158332 // red
      },
      {
        title: `Portfolio Moves ≥ 5% | ${data.universeLabel}`,
        description:
          data.portfolioMoves.length
            ? data.portfolioMoves.map(formatQuote).join('\n')
            : 'No holdings exceeded threshold',
        color: 3447003 // blue
      }
    ];

    const discordResult = await postToDiscord(content, embeds);
    const delivered = discordResult === true;
    const error = delivered ? null : discordResult;

    const allAlerts = [
      ...data.gainers.map(q => ({ ...q, type: 'gainer' })),
      ...data.losers.map(q => ({ ...q, type: 'loser' })),
      ...data.portfolioMoves.map(q => ({ ...q, type: 'portfolio' }))
    ];

    for (const alert of allAlerts) {
      await logAlert(
        alert.symbol,
        Number.isFinite(Number(alert.changePercent)) ? Number(alert.changePercent) : null,
        Number.isFinite(Number(alert.price)) ? Number(alert.price) : null,
        alert.currency || 'USD',
        alert.type,
        delivered,
        error,
        data.runtimeName
      );
    }

    console.log(`Logged ${allAlerts.length} daily alerts to database for ${data.runtimeName}`);
  } catch (err) {
    console.error(`runDailyMarketAndPortfolioForBot failed (${botName}):`, err.message);
  }
}

async function runAllBotSignals() {
  const bots = resolveConfiguredAlertBots();
  console.log(`Running All Bot Signals for ${bots.length} bot(s): ${bots.join(', ')}`);
  for (const botName of bots) {
    await runAllBotSignalsForBot(botName);
  }
}

async function runDailyMarketAndPortfolioAlerts() {
  const bots = resolveConfiguredAlertBots();
  console.log(`Running Daily Market and Portfolio alerts for ${bots.length} bot(s): ${bots.join(', ')}`);
  for (const botName of bots) {
    await runDailyMarketAndPortfolioForBot(botName);
  }
}

// ---------- Schedule (Cron format: minute hour * * day-of-week) ----------
// Format: 'minute hour * * 1-5' for weekdays (1=Mon, 5=Fri), timezone: America/New_York

function startDaemonSchedule() {
  // All Bot Signals: after ML pipeline, alphabetical per configured bot list.
  // 8:30 AM ET (intended to complete in 8:30-8:40 window depending on provider latency)
  cron.schedule('30 8 * * 1-5', runAllBotSignals, { timezone: 'America/New_York' });

  // 9:30 AM ET
  cron.schedule('30 9 * * 1-5', runDailyMarketAndPortfolioAlerts, { timezone: 'America/New_York' });

  // 12:00 PM ET
  cron.schedule('0 12 * * 1-5', runDailyMarketAndPortfolioAlerts, { timezone: 'America/New_York' });

  // 3:30 PM ET
  cron.schedule('30 15 * * 1-5', runDailyMarketAndPortfolioAlerts, { timezone: 'America/New_York' });
}

// Manual run for testing:
if (require.main === module) {
  if (RUN_ONCE) {
    const mode = ['signals', 'daily', 'both'].includes(ALERT_MODE) ? ALERT_MODE : 'daily';
    console.log(`🚀 Running one-shot alert mode: ${mode}`);
    const runner = async () => {
      if (mode === 'signals') {
        await runAllBotSignals();
        return;
      }
      if (mode === 'both') {
        await runAllBotSignals();
        await runDailyMarketAndPortfolioAlerts();
        return;
      }
      await runDailyMarketAndPortfolioAlerts();
    };

    runner().finally(async () => {
      if (dbPool) {
        await dbPool.end();
      }
      process.exit(0);
    });
  } else {
    console.log('🚀 Starting TradingView Alerts Service...');
    console.log('📅 Scheduled for Signals: 8:30 AM ET (weekdays)');
    console.log('📅 Scheduled for Daily Market & Portfolio: 9:30 AM, 12:00 PM, 3:30 PM ET (weekdays)');
    console.log(`🧭 Alert bots: ${resolveConfiguredAlertBots().join(', ')} | enforce=${ENFORCE_BOT_UNIVERSE}`);
    console.log(`📡 Signals per bot run: ${ALERT_SIGNALS_PER_BOT}`);
    startDaemonSchedule();
    runDailyMarketAndPortfolioAlerts();
  }
}
