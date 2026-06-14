#fundamental_analysis_mysql
-- companies master
CREATE TABLE IF NOT EXISTS companies (
  id INT AUTO_INCREMENT PRIMARY KEY,
  ticker VARCHAR(16) NOT NULL UNIQUE,
  name VARCHAR(255),
  sector VARCHAR(128),
  industry VARCHAR(128),
  exchange VARCHAR(64),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- raw fundamentals snapshots (Alpha Vantage)
CREATE TABLE IF NOT EXISTS fundamentals_raw (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ticker VARCHAR(16) NOT NULL,
  report_date DATE NOT NULL,
  fiscal_period VARCHAR(32),
  fiscal_year INT,
  currency VARCHAR(8),
  total_revenue DECIMAL(20,2),
  net_income DECIMAL(20,2),
  ebit DECIMAL(20,2),
  ebitda DECIMAL(20,2),
  total_assets DECIMAL(20,2),
  total_equity DECIMAL(20,2),
  total_liabilities DECIMAL(20,2),
  cash_and_equivalents DECIMAL(20,2),
  shares_outstanding DECIMAL(20,2),
  book_value_per_share DECIMAL(20,6),
  price_per_share DECIMAL(20,6), -- to be filled from prices
  enterprise_value DECIMAL(20,2), -- computed
  ticker_fk INT,
  UNIQUE (ticker, report_date)
);

-- daily prices (yfinance)
CREATE TABLE IF NOT EXISTS prices_daily (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ticker VARCHAR(16) NOT NULL,
  date DATE NOT NULL,
  open DECIMAL(20,6),
  high DECIMAL(20,6),
  low DECIMAL(20,6),
  close DECIMAL(20,6),
  adj_close DECIMAL(20,6),
  volume BIGINT,
  UNIQUE (ticker, date)
);

-- derived ratios per report_date
CREATE TABLE IF NOT EXISTS fundamentals_derived (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  ticker VARCHAR(16) NOT NULL,
  report_date DATE NOT NULL,
  pe_ratio DECIMAL(20,6),
  pb_ratio DECIMAL(20,6),
  ev_ebit DECIMAL(20,6),
  ev_ebitda DECIMAL(20,6),
  roa DECIMAL(20,6),
  roi DECIMAL(20,6),
  noi DECIMAL(20,6),
  UNIQUE (ticker, report_date)
);