# Airbyte Data Integration Workflows
# Configuration and documentation for Airbyte data pipelines

## Overview
This folder contains Airbyte integration workflows for automated data synchronization and pipeline management.

## Workflow Structure

### Data Integration DAGs
- `airbyte_data_integration_dags.py` - Main data sync workflows and health monitoring

### Supported Data Sources
- **Yahoo Finance**: Stock prices, market data, financial indicators
- **Banking APIs**: Account balances, transaction data, portfolio holdings
- **News APIs**: Market sentiment, financial news, social media data
- **CSV/Excel Files**: Manual data uploads and batch processing

## Configuration

### Airbyte Server Configuration
```yaml
# Airbyte Configuration (docker-compose-airbyte-simple.yml)
services:
  airbyte-server:
    ports:
      - "8001:8001"  # API endpoint
  airbyte-webapp:
    ports:
      - "8000:80"    # Web UI
```

### Connection Management
```python
# Example connection configuration
AIRBYTE_CONFIG = {
    "api_base": "http://localhost:8001/api/v1",
    "workspace_id": "your-workspace-id",
    "connections": {
        "yahoo_finance": "connection-id-1",
        "banking_data": "connection-id-2",
        "news_sentiment": "connection-id-3"
    }
}
```

## Data Pipeline Architecture

### 1. Source Connectors
- **Yahoo Finance Connector**: Real-time stock data
- **REST API Connector**: Banking and financial service APIs
- **File Connector**: CSV/Excel file processing
- **Database Connector**: External database sync

### 2. Destination Connectors
- **MySQL**: Primary data warehouse
- **CSV Files**: Temporary data storage
- **S3 Compatible**: Long-term data archival

### 3. Data Transformation
- **Normalization**: Basic data cleaning and formatting
- **Custom DBT Models**: Advanced transformations
- **Field Mapping**: Source to destination field mapping

## Workflow Scheduling

### Sync Frequencies
- **Market Data**: Every 5 minutes during trading hours
- **Portfolio Data**: Hourly updates
- **News Sentiment**: Every 15 minutes
- **Historical Data**: Daily batch loads

### Dependency Management
```python
# Example DAG dependencies
market_data_sync >> portfolio_calculation >> trading_signals
news_sentiment_sync >> sentiment_analysis >> trading_signals
```

## Data Quality Monitoring

### Automated Checks
- **Freshness**: Data arrival within expected timeframes
- **Completeness**: Required fields are populated
- **Accuracy**: Data validation against known ranges
- **Consistency**: Cross-source data reconciliation

### Alert Conditions
- Missing data for > 30 minutes
- Data quality scores below 95%
- Connection failures > 3 consecutive attempts
- Sync duration exceeding normal thresholds

## Connection Configuration Examples

### Yahoo Finance Connection
```json
{
  "name": "Yahoo Finance - Stock Data",
  "source": {
    "sourceDefinitionId": "yahoo-finance-source",
    "connectionConfiguration": {
      "symbols": ["AAPL", "GOOGL", "MSFT", "TSLA"],
      "interval": "5m",
      "period": "1d",
      "api_key": "${YAHOO_FINANCE_API_KEY}"
    }
  },
  "destination": {
    "destinationDefinitionId": "mysql-destination",
    "connectionConfiguration": {
      "host": "mysql",
      "port": 3306,
      "database": "mansa_bot",
      "username": "airflow",
      "password": "${MYSQL_PASSWORD}"
    }
  }
}
```

### Banking API Connection
```json
{
  "name": "Banking API - Portfolio Data", 
  "source": {
    "sourceDefinitionId": "rest-api-source",
    "connectionConfiguration": {
      "base_url": "${BANKING_API_BASE_URL}",
      "auth": {
        "type": "oauth2",
        "client_id": "${BANKING_CLIENT_ID}",
        "client_secret": "${BANKING_CLIENT_SECRET}"
      },
      "endpoints": [
        "/accounts",
        "/transactions", 
        "/holdings"
      ]
    }
  }
}
```

## Troubleshooting

### Common Connection Issues
1. **Authentication Failures**
   - Verify API keys and credentials
   - Check OAuth token expiration
   - Validate connection permissions

2. **Sync Failures** 
   - Check source system availability
   - Verify network connectivity
   - Review sync configuration

3. **Performance Issues**
   - Optimize sync frequency
   - Implement incremental syncs
   - Add data partitioning

### Monitoring and Logging
- **Airbyte UI**: http://localhost:8000
- **Connection Logs**: Available in Airbyte UI
- **Airflow Integration**: DAG logs for automated triggers
- **Custom Metrics**: Sync duration, record counts, error rates

## Best Practices

### 1. Connection Design
- Use incremental sync when possible
- Implement proper error handling
- Set appropriate timeout values
- Configure retry logic

### 2. Data Security
- Use environment variables for credentials
- Implement data encryption in transit
- Regular credential rotation
- Audit access logs

### 3. Performance Optimization
- Batch processing for large datasets
- Parallel processing for independent sources
- Data compression for network efficiency
- Smart scheduling to avoid peak hours

### 4. Maintenance
- Regular connection health checks
- Performance monitoring and alerting
- Backup and disaster recovery planning
- Documentation and runbook maintenance

## Integration with Other Services

### Airflow Integration
- Automated trigger of Airbyte syncs
- DAG dependencies based on data availability
- Error handling and retry logic
- Monitoring integration

### MLflow Integration  
- Data lineage tracking
- Model feature data sourcing
- Experiment reproducibility
- Data versioning