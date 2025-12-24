# Airflow DAGs Configuration
# Configuration and documentation for Bentley Budget Bot Airflow workflows

## Overview
This folder contains all Airflow DAGs for the Bentley Budget Bot project, organized by workflow type and functionality.

## DAG Structure

### Core Trading DAGs
- `bentleybot_trading_dag.py` - Main trading workflow with technical analysis and MLflow integration

### Airflow Configuration
- **Executor**: CeleryExecutor for scalable task execution
- **Database**: MySQL backend for metadata storage
- **Broker**: Redis for task queuing
- **Scheduler**: Hourly execution for trading strategies

## Environment Variables

Required environment variables for DAG execution:

```bash
# Database Configuration
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=mysql+pymysql://root:root@mysql:3306/mansa_bot

# Celery Configuration  
AIRFLOW__CELERY__BROKER_URL=redis://redis:6379/0
AIRFLOW__CELERY__RESULT_BACKEND=db+mysql://root:root@mysql:3306/mansa_bot

# MLflow Integration
MLFLOW_TRACKING_URI=http://mlflow:5000

# Airbyte Integration
AIRBYTE_API_URL=http://localhost:8001
```

## DAG Development Guidelines

### 1. Naming Conventions
- Use descriptive names with underscores: `trading_strategy_dag.py`
- Include environment prefix for multi-env deployments
- Add version numbers for major changes: `v2_trading_dag.py`

### 2. Task Dependencies
- Use clear task IDs that describe the operation
- Implement proper error handling and retries
- Add meaningful logging for debugging

### 3. Data Flow
```
Data Source → Airbyte Sync → Data Processing → ML Analysis → Trading Decision → MLflow Logging
```

### 4. Best Practices
- Always use `@st.cache_data` for expensive operations
- Implement circuit breakers for external API calls
- Use Airflow Variables for configuration management
- Add comprehensive docstrings and comments

## Testing DAGs

### Local Testing
```bash
# Test DAG syntax
python -m py_compile bentleybot_trading_dag.py

# Test individual tasks
airflow tasks test bentleybot_dag trigger_airbyte 2025-11-21
```

### Integration Testing
```bash
# Test full DAG execution
airflow dags backfill bentleybot_dag -s 2025-11-21 -e 2025-11-21
```

## Monitoring and Alerting

### Key Metrics to Monitor
- DAG execution success rate
- Task execution duration
- Data freshness and quality
- Trading signal accuracy
- MLflow experiment tracking

### Alert Conditions
- DAG failure rate > 5%
- Task execution time > 30 minutes
- Data pipeline delays > 1 hour
- Trading API connectivity issues

## Deployment

### Development Environment
```bash
# Start Airflow services
docker-compose -f docker-compose-airflow.yml up -d

# Access Airflow UI
http://localhost:8080 (admin/admin)
```

### Production Deployment
- Use Kubernetes Executor for production scaling
- Implement proper secrets management
- Configure backup strategies for DAG history
- Set up external monitoring and alerting

## Troubleshooting

### Common Issues
1. **Import Errors**: Check Python package dependencies in requirements.txt
2. **Database Connections**: Verify MySQL connectivity and credentials
3. **External API Timeouts**: Implement retry logic with exponential backoff
4. **Memory Issues**: Optimize data processing tasks and use chunking

### Log Locations
- Airflow logs: `/opt/airflow/logs`
- DAG processor logs: Airflow UI → Browse → Logs
- Task instance logs: Airflow UI → DAG → Task → Logs

## Integration Points

### MLflow Integration
- Experiment tracking for model performance
- Model versioning and deployment
- Artifact storage for trading signals

### Airbyte Integration  
- Automated data pipeline triggering
- Connection health monitoring
- Data quality validation

### External APIs
- Yahoo Finance for market data
- Banking APIs for portfolio data
- News APIs for sentiment analysis