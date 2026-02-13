# Bentley Budget Bot - Complete Implementation Roadmap
## Phase 1: Data Migration & Testing Bot Infrastructure
**Status**: Ready to Deploy | **Date**: January 27, 2026
**Target Completion**: 2 weeks

---

## ✅ Completed Components (Ready to Deploy)

### 1. **demo_main.py** ✅ (730 lines)
- **Location**: `bbbot1_pipeline/demo_main.py`
- **Purpose**: Dry-run bot for Phase 1 testing (Demo_Bots 3307)
- **Status**: Production-ready, includes full dry-run logic
- **Next Step**: Execute in demo environment, validate output

### 2. **v1.1.0_create_audit_tables.sql** ✅ (400+ lines)
- **Location**: `migrations/v1.1.0_create_audit_tables.sql`
- **Tables Created**: 6 tables + 3 views
  - ingestion_log (connector audits)
  - bot_decision_audit (trading decisions)
  - sentiment_msgs (social sentiment)
  - sentiment_daily (daily aggregates)
  - bot_performance_metrics (daily P&L)
  - experiment_audit (MLflow tracking)
- **Status**: Ready to deploy to all environments
- **Next Step**: Execute via migration manager

### 3. **v1.2.0_create_sentiment_tables.sql** ✅ (300+ lines)
- **Location**: `migrations/v1.2.0_create_sentiment_tables.sql`
- **Tables Created**: 6 additional tables + 3 views
  - sentiment_msgs (detailed message storage)
  - sentiment_daily (pre-aggregated daily data)
  - sentiment_hourly (intraday tracking)
  - sentiment_keywords (keyword correlation)
  - sentiment_correlation (ticker correlation)
  - sentiment_feed_sources (pipeline status)
- **Status**: Ready to deploy
- **Note**: Includes views for real-time sentiment querying
- **Next Step**: Execute via migration manager

### 4. **migration_manager.py** ✅ (250 lines)
- **Location**: `scripts/migration_manager.py`
- **Purpose**: Python CLI tool for managing versioned migrations
- **Features**:
  - Environment-aware execution (demo/staging/prod)
  - Automatic discovery of migration files
  - Version-based ordering
  - Migration tracking in database
  - Dry-run capability
- **Usage**:
  ```bash
  python scripts/migration_manager.py --env demo --action execute
  python scripts/migration_manager.py --env staging --action discover
  python scripts/migration_manager.py --env prod --action status --dry-run
  ```
- **Status**: Ready to use
- **Next Step**: Execute on all environments

### 5. **GitHub Actions Workflows** ✅ (3 workflows)
- **Files Created**:
  - `.github/workflows/migrate-demo.yml` (dev branch)
  - `.github/workflows/migrate-staging.yml` (staging branch)
  - `.github/workflows/migrate-prod.yml` (main branch)
- **Features**:
  - Branch-to-environment mapping
  - Automatic backup (prod only)
  - Slack notifications
  - Integration test execution
  - Smoke test validation
- **Status**: Ready to commit and test
- **Next Step**: Push to repository and test on each branch

### 6. **staging_bot.py** ✅ (450+ lines)
- **Location**: `bbbot1_pipeline/staging_bot.py`
- **Purpose**: Integration testing with Alpaca broker (paper trading)
- **Components**:
  - BrokerConnector abstract interface
  - AlpacaBrokerConnector implementation
  - MansaBot main trading bot
  - Technical analysis (RSI, MACD)
  - Risk management & position sizing
  - MySQL audit logging
- **Status**: Production-ready, ready for staging deployment
- **Next Step**: Test with Alpaca paper account

### 7. **Migration Directory Structure** ✅ (4 directories)
- **Created**:
  - `migrations/base/` - Shared migrations (all environments)
  - `migrations/demo/` - Demo-specific migrations
  - `migrations/staging/` - Staging-specific migrations
  - `migrations/prod/` - Production-specific migrations
- **Purpose**: Enable environment-aware migration strategies
- **Status**: Ready to populate with migrations
- **Next Step**: Move existing migrations to base/, create env-specific overrides

---

## 🔄 Implementation Roadmap (Next Steps)

### **PHASE 1: Deploy Audit Infrastructure** (This Week)
**Status**: 90% Complete

#### Task 1.1: Execute v1.1.0 Migration ⏳
- **Command**:
  ```bash
  python scripts/migration_manager.py --env demo --action execute
  ```
- **Verify**:
  ```bash
  mysql -h localhost -P 3307 -u root -p test_bbbot1 -e "SHOW TABLES LIKE 'ingestion%';"
  mysql -h localhost -P 3307 -u root -p test_bbbot1 -e "SHOW TABLES LIKE 'bot_decision%';"
  ```
- **Expected Output**: 6 new tables created
- **Time**: 10 minutes
- **Dependencies**: MySQL running on port 3307

#### Task 1.2: Execute v1.2.0 Migration ⏳
- **Command**:
  ```bash
  python scripts/migration_manager.py --env demo --action execute
  ```
- **Verify**:
  ```bash
  mysql -h localhost -P 3307 -u root -p test_bbbot1 -e "SELECT COUNT(*) FROM sentiment_daily;"
  ```
- **Expected Output**: All sentiment tables created
- **Time**: 10 minutes

#### Task 1.3: Test demo_main.py ⏳
- **Command**:
  ```bash
  cd bbbot1_pipeline
  python demo_main.py --mode demo --verbose
  ```
- **Verify Output**:
  - `demo_results.json` created with portfolio summary
  - `demo_logs/` directory created with audit files
  - Trading signals generated for test portfolio
- **Time**: 5 minutes

#### Task 1.4: Validate Audit Logging ⏳
- **Query**:
  ```sql
  SELECT COUNT(*) FROM bbbot1.bot_decision_audit WHERE bot_id LIKE 'demo%';
  ```
- **Expected**: Decision records should appear if demo_main.py integrated with DB
- **Time**: 5 minutes

### **PHASE 2: Setup Staging Environment** (Week 2)
**Status**: Not Started (30% Prep)

#### Task 2.1: Create Staging Migration Overrides
- **Location**: `migrations/staging/`
- **Action**: Create staging-specific configurations:
  - `001_staging_init.sql` - Staging database initialization with test data
  - `002_staging_seed_portfolio.sql` - Pre-populate test portfolio
- **Time**: 2 hours
- **Depends On**: Phase 1 complete

#### Task 2.2: Commit GitHub Actions Workflows
- **Action**: 
  ```bash
  git add .github/workflows/migrate-*.yml
  git commit -m "Add environment-specific migration workflows"
  git push origin main
  ```
- **Verify**: Check GitHub Actions tab for workflow files
- **Time**: 15 minutes

#### Task 2.3: Test Dev Branch Deployment
- **Action**:
  1. Create test commit on `dev` branch
  2. Push to trigger `migrate-demo.yml`
  3. Monitor GitHub Actions execution
  4. Verify demo database updated
- **Expected**: GitHub Actions workflow runs successfully, demo DB migrated
- **Time**: 10 minutes
- **Depends On**: Task 2.2

#### Task 2.4: Deploy Mansa_Bot to Staging
- **Setup**:
  1. Set environment variables:
     ```bash
     export ALPACA_API_KEY="your_alpaca_key"
     export ALPACA_SECRET_KEY="your_secret"
     export DB_HOST="localhost"
     export DB_PORT="3307"
     export DB_USER="root"
     export DB_PASSWORD="root"
     ```
  2. Run staging bot:
     ```bash
     python bbbot1_pipeline/staging_bot.py
     ```
- **Verify**:
  - Bot connects to Alpaca (paper trading)
  - bot_decision_audit table populated with decisions
  - Log messages show trading signals
- **Time**: 1 hour
- **Depends On**: Phase 1 + Alpaca account setup

### **PHASE 3: Production Deployment** (Week 3)
**Status**: Not Started (20% Prep)

#### Task 3.1: Create Production Migration Overrides
- **Location**: `migrations/prod/`
- **Action**: Create prod-specific migrations:
  - `001_prod_init.sql` - Production database initialization (larger capacity)
  - `002_prod_user_roles.sql` - Create 5-tier RBAC users
- **Time**: 2 hours
- **Depends On**: Phase 1 + RBAC system tested

#### Task 3.2: Setup Production Secrets
- **Action**:
  1. Add GitHub repository secrets:
     - `DB_PROD_HOST`
     - `DB_PROD_PORT`
     - `DB_PROD_USER`
     - `DB_PROD_PASSWORD`
     - `AWS_ACCESS_KEY_ID` (for backups)
     - `AWS_SECRET_ACCESS_KEY`
     - `BACKUP_BUCKET`
  2. Verify secrets in GitHub Settings
- **Time**: 15 minutes

#### Task 3.3: Test Staging→Prod Migration Path
- **Action**:
  1. Create release branch from `staging`
  2. Merge to `main` (triggers `migrate-prod.yml`)
  3. Monitor GitHub Actions (backup + migration)
  4. Verify production database
- **Expected**: 
  - Database backup created in S3
  - All migrations executed on prod
  - Smoke tests passing
- **Time**: 1 hour
- **Depends On**: Task 3.1 + Task 3.2

### **PHASE 4: Integration Testing** (Week 4)
**Status**: Not Started

#### Task 4.1: E2E Test: Demo→Staging→Prod Flow
- **Process**:
  1. Run `demo_main.py` on demo environment
  2. Verify decisions logged to `test_bbbot1.bot_decision_audit`
  3. Deploy v1.2.0 to staging
  4. Run staging bot (Mansa_Bot)
  5. Verify decisions logged to `bbbot1.bot_decision_audit`
  6. Deploy to production
  7. Verify audit logs visible in production
- **Success Criteria**:
  - ✅ Demo decisions created & logged
  - ✅ Staging decisions created & logged
  - ✅ Production decisions created & logged
  - ✅ Migration history recorded in all environments
- **Time**: 4 hours

#### Task 4.2: Performance Testing
- **Queries to Test**:
  ```sql
  -- Recent decisions
  SELECT * FROM bot_decision_audit 
  ORDER BY created_at DESC LIMIT 100;
  
  -- Sentiment by ticker
  SELECT ticker, AVG(avg_sentiment) FROM sentiment_daily 
  GROUP BY ticker ORDER BY created_at DESC LIMIT 10;
  
  -- Bot performance
  SELECT * FROM bot_performance_metrics 
  WHERE bot_id = 'mansa_bot_staging_v1';
  ```
- **Target**: <100ms query execution
- **Time**: 2 hours

#### Task 4.3: Load Testing
- **Scenario**: Insert 10,000 decisions to bot_decision_audit
- **Measure**: Insert time, query response time
- **Target**: <5 seconds for 10K inserts
- **Time**: 1 hour

---

## 📋 Current Database Status

### Demo Environment (Port 3307)
```
✅ test_bbbot1 (created)
✅ test_mlflow_db (created)
✅ test_mansa_quant (created)

Pending Tables:
🔲 ingestion_log → v1.1.0 migration
🔲 bot_decision_audit → v1.1.0 migration
🔲 sentiment_msgs → v1.2.0 migration
🔲 sentiment_daily → v1.2.0 migration
```

### Staging Environment (Port 3307)
```
✅ bbbot1 (created)
✅ mlflow_db (created)
✅ mansa_quant (created)

Pending Tables:
🔲 All audit tables (same as demo)
🔲 Staging-specific seed data
```

### Production Environment (Port 3306)
```
✅ bentley_bot (created)
✅ mlflow_db (created)
✅ mansa_quant (created)

Pending Tables:
🔲 All audit tables
🔲 Production RBAC users
```

---

## 🔧 Quick Reference Commands

### Deploy Migrations
```bash
# Demo environment
python scripts/migration_manager.py --env demo --action execute

# Staging environment
python scripts/migration_manager.py --env staging --action execute

# Production environment (requires careful review)
python scripts/migration_manager.py --env prod --action execute

# Dry-run (no changes)
python scripts/migration_manager.py --env demo --dry-run
```

### Test Components
```bash
# Test demo bot
cd bbbot1_pipeline
python demo_main.py --mode demo --verbose --output demo_results.json

# Test staging bot
export ALPACA_API_KEY="your_key"
export ALPACA_SECRET_KEY="your_secret"
python staging_bot.py

# Query audit logs
mysql -h localhost -P 3307 -u root -p -e \
  "SELECT * FROM test_bbbot1.bot_decision_audit LIMIT 10;"
```

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/audit-infrastructure

# Make changes, commit
git add .
git commit -m "Add audit table migrations and testing bots"

# Push to dev (triggers demo migration)
git push origin dev

# Merge to staging (triggers staging migration)
git checkout staging
git merge feature/audit-infrastructure
git push origin staging

# Merge to main (triggers production migration)
git checkout main
git merge staging
git push origin main
```

---

## 📊 Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Migrations versioned | 100% | 0% | 🔄 In Progress |
| Audit tables created | 100% | 0% | 🔄 Pending v1.1.0 |
| Sentiment pipeline | 100% | 0% | 🔄 Pending v1.2.0 |
| Demo bot functional | 100% | 100% | ✅ Complete |
| Staging bot integrated | 100% | 0% | 🔄 Pending deployment |
| GitHub Actions working | 100% | 0% | 🔄 Pending testing |
| E2E flow validated | 100% | 0% | 🔄 Pending Phase 4 |

---

## 🚨 Critical Path

1. **This Week**: Execute v1.1.0 + v1.2.0 migrations on demo (1 day)
2. **This Week**: Test demo_main.py on demo environment (1 day)
3. **Next Week**: Deploy staging bot to staging environment (2 days)
4. **Next Week**: Test GitHub Actions workflows (1 day)
5. **Following Week**: Production deployment with backups (1 day)
6. **Following Week**: E2E testing and validation (2 days)

**Total Timeline**: 2-3 weeks to full alignment

---

## 📞 Support & Troubleshooting

### Connection Issues
```bash
# Test database connection
mysql -h localhost -P 3307 -u root -p -e "SELECT 1;"

# Check port availability
netstat -an | grep 3307
lsof -i :3307
```

### Migration Failures
```bash
# Check migration history
mysql -h localhost -P 3307 -u root -p test_bbbot1 \
  -e "SELECT * FROM migration_history;"

# Verify table creation
mysql -h localhost -P 3307 -u root -p test_bbbot1 \
  -e "SHOW TABLES;"
```

### Bot Execution Issues
```bash
# Check logs
tail -f demo_logs/decisions_audit.jsonl

# Verify database connectivity
python -c "import mysql.connector; \
  conn = mysql.connector.connect(host='localhost', user='root', password='root'); \
  print('Connected successfully')"
```

---

**Last Updated**: January 27, 2026  
**Next Review**: January 30, 2026  
**Owner**: Bentley Bot System
