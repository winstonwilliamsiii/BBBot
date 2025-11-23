# Stocktwits Sentiment Pipeline - Complete Setup Guide

## 📋 Overview

This guide walks you through setting up a complete pipeline for streaming Stocktwits sentiment data:

**Pipeline Flow:**
```
Stocktwits Website → Airbyte Source Connector → MySQL → Airflow DAG → MLflow (optional)
```

## 📁 Files Created

### Airbyte Source Connector (`airbyte-source-stocktwits/`)
1. **`source.py`** - Airbyte protocol-compliant Python source
2. **`spec.json`** - Connector specification
3. **`catalog.json`** - Data stream catalog
4. **`config.json`** - Configuration (tickers to track)
5. **`Dockerfile`** - Docker image definition
6. **`schema.sql`** - MySQL table schema
7. **`stocktwits_sentiment_scraper.py`** - Original scraper (reference)

### Airflow DAG
8. **`dags/stocktwits_sentiment_dag.py`** - Orchestration DAG

---

## 🚀 Setup Steps

### Step 1: Create MySQL Table

```powershell
# Create the sentiment data table
docker exec -i bentley-mysql mysql -uroot -proot mansa_bot < airbyte-source-stocktwits/schema.sql

# Verify table creation
docker exec bentley-mysql mysql -uroot -proot mansa_bot -e "DESCRIBE stocktwits_sentiment;"
```

**Expected output:**
```
+------------------+---------------+------+-----+
| Field            | Type          | Null | Key |
+------------------+---------------+------+-----+
| id               | int           | NO   | PRI |
| ticker           | varchar(10)   | NO   | MUL |
| sentiment_score  | decimal(5,4)  | YES  |     |
| bullish_count    | int           | YES  |     |
| bearish_count    | int           | YES  |     |
| total_messages   | int           | YES  |     |
| scraped_at       | timestamp     | NO   | MUL |
| url              | varchar(500)  | YES  |     |
| created_at       | timestamp     | YES  |     |
+------------------+---------------+------+-----+
```

### Step 2: Build Docker Image

```powershell
# Navigate to the source directory
cd airbyte-source-stocktwits

# Build the Docker image
docker build -t airbyte/source-stocktwits:0.1.0 .

# Verify image created
docker images | Select-String "stocktwits"
```

### Step 3: Test Airbyte Source Locally

```powershell
# Test spec command
docker run --rm airbyte/source-stocktwits:0.1.0 spec

# Test check command (validates config)
docker run --rm -v ${PWD}:/data airbyte/source-stocktwits:0.1.0 check --config /data/config.json

# Test discover command (shows available streams)
docker run --rm -v ${PWD}:/data airbyte/source-stocktwits:0.1.0 discover --config /data/config.json

# Test read command (fetch actual data)
docker run --rm -v ${PWD}:/data airbyte/source-stocktwits:0.1.0 read --config /data/config.json --catalog /data/catalog.json
```

**Expected output for `read`:**
```json
{"type": "RECORD", "record": {"stream": "sentiment_scores", "data": {"ticker": "AMZN", "sentiment_score": 0.15, ...}}}
{"type": "RECORD", "record": {"stream": "sentiment_scores", "data": {"ticker": "TSLA", "sentiment_score": 0.32, ...}}}
{"type": "STATE", "state": {"data": {"sentiment_scores": {"last_sync": "2025-11-23T..."}}}}
```

### Step 4: Configure Tickers

Edit `airbyte-source-stocktwits/config.json`:
```json
{
  "tickers": ["AMZN", "TSLA", "AAPL", "NVDA", "MSFT", "GOOGL", "META"],
  "user_agent": "Mozilla/5.0 (compatible; BentleyBot/1.0)"
}
```

### Step 5: Mount Source in Airflow

Update `docker-compose-airflow.yml` to mount the source directory:

```yaml
services:
  airflow-webserver:
    volumes:
      - ./dags:/opt/airflow/dags
      - ./airbyte-source-stocktwits:/opt/airflow/airbyte-source-stocktwits  # Add this line
      - ./airflow_config/logs:/opt/airflow/logs
      - ./data:/opt/airflow/data

  airflow-scheduler:
    volumes:
      - ./dags:/opt/airflow/dags
      - ./airbyte-source-stocktwits:/opt/airflow/airbyte-source-stocktwits  # Add this line
      - ./airflow_config/logs:/opt/airflow/logs
      - ./data:/opt/airflow/data

  airflow-worker:
    volumes:
      - ./dags:/opt/airflow/dags
      - ./airbyte-source-stocktwits:/opt/airflow/airbyte-source-stocktwits  # Add this line
      - ./airflow_config/logs:/opt/airflow/logs
      - ./data:/opt/airflow/data
```

### Step 6: Restart Airflow

```powershell
# Restart Airflow to pick up new volumes and DAG
docker-compose -f docker-compose-airflow.yml restart

# Wait for services to be ready
Start-Sleep -Seconds 15

# Verify DAG loaded
docker exec bentley-airflow-scheduler airflow dags list | Select-String "stocktwits"
```

### Step 7: Trigger the DAG

```powershell
# Trigger manual run
docker exec bentley-airflow-scheduler airflow dags trigger stocktwits_sentiment_pipeline

# Monitor execution
docker exec bentley-airflow-scheduler airflow dags list-runs -d stocktwits_sentiment_pipeline

# View task logs
docker exec bentley-airflow-scheduler airflow tasks test stocktwits_sentiment_pipeline scrape_stocktwits 2025-11-23
```

### Step 8: Verify Data in MySQL

```powershell
# Check inserted records
docker exec bentley-mysql mysql -uroot -proot mansa_bot -e "
SELECT ticker, sentiment_score, bullish_count, bearish_count, 
       total_messages, scraped_at 
FROM stocktwits_sentiment 
ORDER BY scraped_at DESC 
LIMIT 10;"
```

---

## 🔧 Airbyte Cloud Integration (Optional)

If you want to use Airbyte Cloud instead of the local connector:

### Step 1: Push Docker Image to Registry

```powershell
# Tag for Docker Hub
docker tag airbyte/source-stocktwits:0.1.0 yourusername/source-stocktwits:0.1.0

# Login to Docker Hub
docker login

# Push image
docker push yourusername/source-stocktwits:0.1.0
```

### Step 2: Register Custom Connector in Airbyte Cloud

1. Go to: https://cloud.airbyte.com
2. Navigate to: **Settings** → **Sources** → **Custom Connectors**
3. Click: **+ New Connector**
4. Fill in:
   - **Name**: Stocktwits Sentiment
   - **Docker Image**: `yourusername/source-stocktwits:0.1.0`
   - **Docker Tag**: `0.1.0`
   - **Documentation URL**: https://stocktwits.com

### Step 3: Create Connection in Airbyte Cloud

1. **Sources** → **+ New Source**
2. Select: **Stocktwits Sentiment** (your custom connector)
3. Configure:
   - **Tickers**: ["AMZN", "TSLA", "AAPL"]
   - **User Agent**: Mozilla/5.0 (compatible; BentleyBot/1.0)
4. Click: **Test Connection**

5. **Destinations** → Select existing **MySQL** destination
6. **Connections** → **+ New Connection**
   - **Source**: Stocktwits Sentiment
   - **Destination**: MySQL (mansa_bot database)
   - **Stream**: sentiment_scores → stocktwits_sentiment table
   - **Sync Mode**: Full Refresh (overwrite)
   - **Schedule**: Every 1 hour

---

## 📊 Airflow DAG Details

### DAG: `stocktwits_sentiment_pipeline`

**Schedule**: `@hourly` (runs every hour)

**Tasks**:
1. **scrape_stocktwits** - Runs the Airbyte source, fetches data, stores in MySQL
2. **log_results** - Logs how many records were inserted

**Datasets**:
- **Produces**: `Dataset("mysql://mansa_bot/stocktwits_sentiment")`
- Can trigger downstream DAGs (KNIME, MLflow) via dataset connections

### Monitoring

**Airflow UI**: http://localhost:8080
- View: DAGs → stocktwits_sentiment_pipeline
- Check: Graph view for task flow
- Monitor: Logs for each task

**Command Line**:
```powershell
# List recent runs
docker exec bentley-airflow-scheduler airflow dags list-runs -d stocktwits_sentiment_pipeline

# Check task status
docker exec bentley-airflow-scheduler airflow tasks states-for-dag-run stocktwits_sentiment_pipeline <run_id>
```

---

## 🔗 Integration with Existing Pipeline

### Connect to Your Orchestration

Update `dags/stocktwits_sentiment_dag.py` to connect with your pipeline:

```python
from airflow.datasets import Dataset

# Add dataset outlet
stocktwits_dataset = Dataset("mysql://mansa_bot/stocktwits_sentiment")

# In your DAG definition
scrape_task = PythonOperator(
    task_id='scrape_stocktwits',
    python_callable=run_stocktwits_scraper,
    outlets=[stocktwits_dataset]  # Triggers downstream DAGs
)
```

### Connect to KNIME/MLflow

Create a new DAG that consumes this dataset:

```python
from airflow.datasets import Dataset

stocktwits_dataset = Dataset("mysql://mansa_bot/stocktwits_sentiment")

with DAG(
    'sentiment_analysis_pipeline',
    schedule=[stocktwits_dataset],  # Trigger when data available
    ...
) as dag:
    # Process sentiment data
    analyze_task = PythonOperator(...)
```

---

## 🐛 Troubleshooting

### Issue: "Module 'requests' not found"

**Solution**: Ensure Dockerfile installs dependencies
```dockerfile
RUN pip install --no-cache-dir requests beautifulsoup4 lxml
```

### Issue: "Table 'stocktwits_sentiment' doesn't exist"

**Solution**: Run schema.sql
```powershell
docker exec -i bentley-mysql mysql -uroot -proot mansa_bot < airbyte-source-stocktwits/schema.sql
```

### Issue: "Permission denied" when scraping

**Solution**: Verify User-Agent in config.json
```json
{"user_agent": "Mozilla/5.0 (compatible; BentleyBot/1.0)"}
```

### Issue: DAG not showing in Airflow UI

**Solution**: Check DAG syntax and restart scheduler
```powershell
python -m py_compile dags/stocktwits_sentiment_dag.py
docker-compose -f docker-compose-airflow.yml restart airflow-scheduler
```

### Issue: "Connection refused" to MySQL

**Solution**: Ensure using internal Docker network name `mysql` not `localhost`
```python
mysql_config = {"host": "mysql", "port": 3306, ...}
```

---

## 📈 Data Schema

### Table: `stocktwits_sentiment`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Primary key |
| `ticker` | VARCHAR(10) | Stock ticker (AMZN, TSLA, etc.) |
| `sentiment_score` | DECIMAL(5,4) | Normalized score (-1 to 1) |
| `bullish_count` | INT | Number of bullish messages |
| `bearish_count` | INT | Number of bearish messages |
| `total_messages` | INT | Total message count |
| `scraped_at` | TIMESTAMP | When data was scraped |
| `url` | VARCHAR(500) | Source URL |
| `created_at` | TIMESTAMP | Record creation time |

**Indexes**:
- `ticker` - Fast lookups by ticker
- `scraped_at` - Time-based queries
- `ticker, scraped_at` - Combined index for filtering

---

## 🎯 Next Steps

1. ✅ **Test the pipeline**: Run manual trigger and verify data
2. ✅ **Monitor hourly runs**: Check Airflow UI for scheduled executions
3. ✅ **Add more tickers**: Edit `config.json` with additional symbols
4. ✅ **Connect to MLflow**: Log sentiment scores as experiments
5. ✅ **Create visualizations**: Build Grafana dashboard for sentiment trends
6. ✅ **Set up alerts**: Configure Airflow notifications for failures

---

## 🔐 Security Notes

- ✅ **Rate limiting**: Stocktwits may rate-limit excessive requests
- ✅ **User-Agent**: Always use a descriptive User-Agent string
- ✅ **Terms of Service**: Ensure compliance with Stocktwits ToS
- ✅ **Data retention**: Consider archiving old sentiment data

---

## 📚 Resources

- **Airbyte Protocol**: https://docs.airbyte.com/connector-development
- **Stocktwits**: https://stocktwits.com
- **Airflow Datasets**: https://airflow.apache.org/docs/apache-airflow/stable/concepts/datasets.html
- **Docker Build**: https://docs.docker.com/engine/reference/commandline/build/

---

✅ **Your Stocktwits sentiment pipeline is ready to stream data every hour!** 🚀
