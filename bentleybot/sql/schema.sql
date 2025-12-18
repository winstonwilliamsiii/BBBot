-- Schema for Bentley Budget Bot
-- Define your tables and relationships here

-- Updated schema based on eraser_p_budget_schemas.mysql

CREATE TABLE Income (
    IncomeID VARCHAR(255) PRIMARY KEY,
    capital_gainsID VARCHAR(255),
    Payroll VARCHAR(255),
    Transfer VARCHAR(255),
    Dividend VARCHAR(255),
    SBA VARCHAR(255),
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Investment (
    capital_gainsID VARCHAR(255) PRIMARY KEY,
    IncomeID VARCHAR(255),
    IBKR VARCHAR(255),
    Webull VARCHAR(255),
    NinjaTrader VARCHAR(255),
    MTQ5 VARCHAR(255),
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE PersonalExpenses (
    personal_expID VARCHAR(255) PRIMARY KEY,
    MiscID VARCHAR(255),
    p_mediaID VARCHAR(255),
    HealthCare VARCHAR(255),
    Food VARCHAR(255),
    Miscellaneous VARCHAR(255),
    Rent VARCHAR(255),
    Utilities VARCHAR(255),
    Telecom VARCHAR(255),
    Transportation VARCHAR(255),
    Media_Internet VARCHAR(255),
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

#Personal Finance and Investment MVP2
// title
title Personal Finance & Investment MVP2 Data Model

// Appwrite tables
users [icon: user, color: yellow]{
  user_id string pk
  email string
  name string
  status string
  created_at timestamp
}

teams [icon: users, color: blue]{
  team_id string pk
  name string
  members string // links to users
}

roles [icon: shield, color: orange]{
  role_id string pk
  name string
  description string
}

permissions [icon: key, color: green]{
  permission_id string pk
  name string
}

// Appwrite Collections
kyc [icon: file-text, color: lightblue]{
  kyc_id string pk
  user_id string
  status string
  submitted_at timestamp
}

payments [icon: credit-card, color: purple]{
  payment_id string pk
  user_id string
  amount decimal
  currency string
  receipt_url string
  created_at timestamp
}

auditlogs [icon: activity, color: red]{
  log_id string pk
  user_id string
  action string
  details string
  timestamp timestamp
}

// MySQL: mydb
accounts [icon: dollar-sign, color: green]{
  account_id int pk
  user_id string
  name string
  type string
  starting_balance decimal
}

transactions [icon: repeat, color: orange]{
  transaction_id int pk
  account_id int
  category_id int
  date date
  amount decimal
  description string
}

categories [icon: tag, color: blue]{
  category_id int pk
  name string
  parent_id int
}

plaid_items [icon: link, color: lightgreen]{
  item_id int pk
  user_id string
  access_token string
  institution_id string
}

// MVP1 Tables: Personal Finance Extensions
personal_expenses [icon: shopping-bag, color: pink]{
  personal_expID int pk
  user_id string
  miscID int
  p_medialD int
  HealthCare decimal
  Food decimal
  Rent decimal
  Utilities decimal
  Telecom decimal
  Transportation decimal
  Media_Internet decimal
}

income [icon: trending-up, color: teal]{
  incomeID int pk
  user_id string
  capital_gainsID int
  Payroll decimal
  Transfer decimal
  Dividend decimal
  SBA decimal
}

miscellaneous [icon: gift, color: orange]{
  miscID int pk
  personal_expID int
  Travel decimal
  Entertainment decimal
  Shopping decimal
  Wellness decimal
  PersonalCare decimal
  Charity decimal
}

media_subscriptions [icon: play, color: purple]{
  p_medialD int pk
  personal_expID int
  Tinder decimal
  USPS decimal
  Apple decimal
  GoogleCloud decimal
  Insurance decimal
  Administrative decimal
  Labor decimal
  Equipment decimal
}

business_expenditure [icon: briefcase, color: blue]{
  business_expID int pk
  SaaSID int
  Transportation decimal
  Insurance decimal
  Administrative decimal
  Labor decimal
  Equipment decimal
  Investment decimal
}

saas [icon: cloud, color: lightblue]{
  saasID int pk
  business_expID int
  GitHub decimal
  Jira decimal
  GCP decimal
  WSJ decimal
  Medium decimal
  LinkedIn decimal
  Coursera decimal
  SkillsBoost decimal
  TradingView decimal
  Lovable decimal
  WordPress decimal
  ScalaHosting decimal
  Quickbooks decimal
  Zoom decimal
  Adobe decimal
}

capital_gains [icon: bar-chart, color: green]{
  capital_gainsID int pk
  incomeID int
  IBKR decimal
  Webull decimal
  NinjaTrader decimal
  MTQ5 decimal
}

// Relationships
accounts.user_id > users.user_id
plaid_items.user_id > users.user_id
transactions.account_id > accounts.account_id
transactions.category_id > categories.category_id

// Personal Finance Extensions Relationships
personal_expenses.user_id > users.user_id
personal_expenses.miscID > miscellaneous.miscID
personal_expenses.p_medialD > media_subscriptions.p_medialD

miscellaneous.personal_expID > personal_expenses.personal_expID
media_subscriptions.personal_expID > personal_expenses.personal_expID

income.user_id > users.user_id
income.capital_gainsID > capital_gains.capital_gainsID
capital_gains.incomeID > income.incomeID

business_expenditure.SaaSID > saas.saasID
saas.business_expID > business_expenditure.business_expID;

#Multi-Tenant Financial Analytics Platform Data Model

// Updated Appwrite tables
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE teams (
    team_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    members TEXT
);

CREATE TABLE roles (
    role_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255),
    description TEXT
);

CREATE TABLE permissions (
    permission_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255)
);

CREATE TABLE kyc (
    kyc_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255),
    status VARCHAR(50),
    submitted_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE payments (
    payment_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255),
    amount DECIMAL(10, 2),
    currency VARCHAR(10),
    receipt_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE auditlogs (
    log_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255),
    action TEXT,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

// Updated MySQL tables
CREATE TABLE accounts (
    account_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(255),
    name VARCHAR(255),
    type VARCHAR(50),
    starting_balance DECIMAL(10, 2),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE transactions (
    transaction_id INT PRIMARY KEY AUTO_INCREMENT,
    account_id INT,
    category_id INT,
    date DATE,
    amount DECIMAL(10, 2),
    description TEXT,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255),
    parent_id INT
);

CREATE TABLE budgets (
    budget_id INT PRIMARY KEY AUTO_INCREMENT,
    category_id INT,
    period VARCHAR(50),
    limit_amount DECIMAL(10, 2),
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE goals (
    goal_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255),
    target_amount DECIMAL(10, 2),
    deadline DATE
);

CREATE TABLE plaid_items (
    item_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(255),
    access_token TEXT,
    institution_id VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

// Updated Relationships
ALTER TABLE teams ADD CONSTRAINT fk_teams_members FOREIGN KEY (members) REFERENCES users(user_id);
ALTER TABLE transactions ADD CONSTRAINT fk_transactions_category FOREIGN KEY (category_id) REFERENCES categories(category_id);
ALTER TABLE budgets ADD CONSTRAINT fk_budgets_category FOREIGN KEY (category_id) REFERENCES categories(category_id);
ALTER TABLE kyc ADD CONSTRAINT fk_kyc_user FOREIGN KEY (user_id) REFERENCES users(user_id);
ALTER TABLE payments ADD CONSTRAINT fk_payments_user FOREIGN KEY (user_id) REFERENCES users(user_id);
ALTER TABLE auditlogs ADD CONSTRAINT fk_auditlogs_user FOREIGN KEY (user_id) REFERENCES users(user_id);
ALTER TABLE runs ADD CONSTRAINT fk_runs_experiment FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id);

-- Additional tables and relationships will follow the same pattern
-- Relationships and foreign keys will be added as per the eraser_p_budget_schemas.mysql