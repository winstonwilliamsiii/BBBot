# Feature/Prediction-Analytics Branch Strategy

## Branch Details
- **Branch Name:** `feature/prediction-analytics`
- **Base Branch:** `main` (stable production)
- **Environment:** bentley-bot-dev service on Railway
- **Target Merge:** To `main` after validation

## Implementation Phases

### Phase 1: Schema Setup & Ingestion Logic
**Files to modify/create:**
- `migrations/20260126_prediction_analytics.sql` ✅ Created
  - Database: `Bentley_Bot` (Port 3306)
  - Schema: `mansa_quant`
  - Tables: `prediction_probabilities`, `sentiment_signals`, `prediction_sentiment_analysis`

**Polymarket/Kalshi Integration:**
- Create: `src/integrations/polymarket_ingestion.py`
- Create: `src/integrations/kalshi_ingestion.py`
- Real-time data feed → prediction_probabilities table
- API polling interval: Configurable (recommend 5-10 min for cost optimization)

### Phase 2: Unit Testing with Mock Data
**Test files:**
- `tests/test_prediction_ingestion.py`
- `tests/test_sentiment_scoring.py`
- `tests/fixtures/mock_polymarket_responses.json`
- `tests/fixtures/mock_kalshi_responses.json`

**Mock data structure:**
```python
{
  "contract_id": "POLY_BTC_2026Q1",
  "source": "Polymarket",
  "implied_probability": 67.50,
  "confidence_score": 0.88,
  "timestamp": "2026-01-26T10:30:00Z"
}
```

### Phase 3: AI Sentiment Scoring Validation
- Integrate with existing ML pipeline (verify with MLflow)
- Validate signal_strength categorization:
  - **weak:** < 0.3 confidence
  - **moderate:** 0.3 - 0.7 confidence
  - **strong:** > 0.7 confidence

### Phase 4: Merge & Production CI/CD
- Create PR from `feature/prediction-analytics` → `main`
- Trigger GitHub Actions:
  - Run all unit tests
  - Validate migration scripts
  - Execute integration tests with bentley-bot-dev
  - Deploy to bentley-core on approval

## Database Connection Matrix

| Environment | Database | Port | Schema | Connection Method | Use Case |
|------------|----------|------|--------|------------------|----------|
| **Docker** (Development) | Bentley_Bot | 3306 | mansa_quant | Container network | Local testing |
| **Docker** (Testing) | Demo_Bot | 3307 | mansa_quant | Container network | Test data isolation |
| **Railway** (Staging) | bentley-bot-dev | 3306 | bot_analytics | Remote connection | bentley-bot-dev service |
| **Railway** (Production) | Bentley_Bot | 3306 | mansa_quant | Remote connection | Production bentley-core |

## Demo_Bot Database Issue (Port 3307)

### Why Port 3307 isn't visible in MySQL Workbench locally:
1. **Docker-only network** - Port 3307 is exposed within the Docker container network, NOT to your host machine
2. **Access method:** Must use Docker commands to query:
   ```bash
   docker-compose exec mysql mysql -u bentley_user -p bentley_password -e "SELECT * FROM Demo_Bot.mansa_quant.prediction_probabilities;"
   ```

### Solution Options:

**Option A: Keep Demo_Bot Docker-only (Recommended for dev)**
```yaml
# docker-compose.yml
services:
  mysql:
    ports:
      - "3306:3306"      # Bentley_Bot - accessible locally & externally
      # 3307 NOT exposed - Demo_Bot stays internal to Docker
```
- ✅ Pros: Isolates test data, prevents accidental production changes
- ❌ Cons: Can't browse in Workbench directly

**Option B: Expose Demo_Bot port (Development flexibility)**
```yaml
# docker-compose.yml
services:
  mysql:
    ports:
      - "3306:3306"      # Bentley_Bot
      - "3307:3307"      # Demo_Bot (requires host port mapping)
```
- Then connect Workbench: `localhost:3307` (user: bentley_user)

**Option C: Use single Bentley_Bot with separate schemas (Recommended production)**
```sql
-- Instead of Demo_Bot database, use:
CREATE SCHEMA bentley_bot_dev;  -- Test data
CREATE SCHEMA bentley_bot_prod; -- Production data
-- Same database = simpler management
```

## Recommendation
Use **Option C** for production readiness:
- Single Bentley_Bot database (Port 3306)
- Separate schemas for environments
- All accessible via single connection string
- Easier CI/CD management

## Git Workflow Summary
```bash
# 1. Switch to feature branch
git checkout feature/prediction-analytics

# 2. Make changes (schema, ingestion logic, tests)
git add .
git commit -m "feat: Add prediction analytics ingestion for Polymarket/Kalshi"

# 3. Push to GitHub for backup
git push origin feature/prediction-analytics

# 4. Test locally with docker-compose
docker-compose up

# 5. Run unit tests
pytest tests/test_prediction_ingestion.py -v

# 6. When complete, PR to main
# Create PR on GitHub → CI/CD validation → Merge to main → Deploy to production
```
