# Bentley Budget Bot - Workflow Management
# Centralized workflow orchestration and management system

## Overview
This directory contains organized workflows for the Bentley Budget Bot's data processing, analytics, and machine learning pipeline. Each workflow environment is designed to handle specific aspects of the financial analysis and trading automation system.

## Workflow Architecture

```
Bentley Budget Bot Workflow Architecture
├── Data Ingestion (Airbyte)
│   └── External APIs → Data Lake → Validated Data
├── Data Processing (Airflow)  
│   └── ETL → Feature Engineering → Data Warehouse
├── Analytics (KNIME)
│   └── Financial Analysis → Risk Assessment → Reporting
└── ML Pipeline (MLflow)
    └── Model Training → Validation → Deployment → Monitoring
```

## Workflow Environments

### 🔄 Airbyte - Data Integration (`/airbyte`)
**Purpose**: Automated data synchronization and ETL pipeline management
- **Data Sources**: Yahoo Finance, Banking APIs, News feeds, Social media
- **Sync Frequency**: Real-time to daily depending on source
- **Output**: Normalized data in MySQL warehouse
- **Key Features**: Connection health monitoring, data quality validation, automated retries

### ⚡ Airflow - Workflow Orchestration (`/airflow`)
**Purpose**: Task scheduling, dependency management, and workflow coordination
- **Core DAG**: `bentleybot_trading_dag.py` - Main trading workflow
- **Schedule**: Hourly execution with configurable intervals
- **Integration**: Coordinates Airbyte, MLflow, and KNIME workflows
- **Key Features**: Celery executor, Redis broker, MySQL metadata store

### 📊 KNIME - Analytics Platform (`/knime`)
**Purpose**: Visual analytics, data science workflows, and enterprise reporting
- **Analytics**: Portfolio risk, technical analysis, market sentiment
- **Execution**: Both standalone and server-based execution
- **Output**: Analysis results, reports, model inputs
- **Key Features**: Visual workflow design, enterprise scalability, automated reporting

### 🧠 MLflow - ML Lifecycle Management (`/mlflow`) 
**Purpose**: Machine learning experiment tracking, model management, and deployment
- **Models**: Price prediction, portfolio optimization, anomaly detection
- **Tracking**: Experiments, parameters, metrics, artifacts
- **Registry**: Model versioning, staging, and production deployment
- **Key Features**: A/B testing, model monitoring, automated retraining

## Data Flow Architecture

### Primary Data Pipeline
```
External APIs 
    ↓ (Airbyte)
Raw Data Lake 
    ↓ (Airflow ETL)
Clean Data Warehouse 
    ↓ (KNIME Analytics)
Analysis Results 
    ↓ (MLflow Training)
ML Models 
    ↓ (Trading Signals)
Portfolio Actions
```

### Real-time Processing
```
Live Market Data → Stream Processing → Risk Monitoring → Alert System
                                  ↓
                              Trading Decisions → Execution → Performance Tracking
```

## Environment Configuration

### Development Setup
```bash
# Start all workflow services
./manage_services.ps1 -Action start

# Access Points:
# - Airflow UI: http://localhost:8080 (admin/admin)
# - Airbyte UI: http://localhost:8000
# - MLflow UI: http://localhost:5000
# - KNIME Server: http://localhost:8080/knime (if configured)
```

### Production Deployment
- **Container Orchestration**: Docker Compose with Kubernetes option
- **Scaling**: Horizontal scaling for compute-intensive workflows
- **Monitoring**: Integrated health checks and alerting
- **Security**: Role-based access control and secure credential management

## Workflow Dependencies

### Service Dependencies
```yaml
MySQL Database:
  - Required by: Airflow (metadata), MLflow (backend), KNIME (data source)
  
Redis:
  - Required by: Airflow (Celery broker)
  
Airbyte:
  - Dependencies: PostgreSQL (internal), Docker runtime
  - Required by: All workflows (data source)
  
MLflow:
  - Dependencies: MySQL (backend store), File system (artifacts)
  - Required by: Airflow (model serving), KNIME (validation data)
```

### Data Dependencies
```yaml
Market Data (Airbyte) → Technical Analysis (KNIME) → Trading Signals (Airflow)
Portfolio Data (Airbyte) → Risk Analysis (KNIME) → Portfolio Optimization (MLflow)
News Data (Airbyte) → Sentiment Analysis (KNIME) → Market Predictions (MLflow)
```

## Configuration Management

### Environment Variables
```bash
# Database Configuration
export MYSQL_HOST=mysql
export MYSQL_PORT=3306
export MYSQL_USER=airflow
export MYSQL_PASSWORD=airflow
export MYSQL_DATABASE=mansa_bot

# Service Endpoints
export AIRFLOW_URL=http://localhost:8080
export AIRBYTE_URL=http://localhost:8000
export MLFLOW_URL=http://localhost:5000
export KNIME_SERVER_URL=http://localhost:8080/knime

# API Keys (use secure secret management in production)
export YAHOO_FINANCE_API_KEY=${YAHOO_API_KEY}
export BANKING_API_KEY=${BANKING_API_KEY}
export NEWS_API_KEY=${NEWS_API_KEY}
```

### Workflow Parameters
```yaml
# Global workflow configuration
workflow_config:
  timezone: "America/New_York"
  market_hours: "09:30-16:00"
  trading_days: "MON,TUE,WED,THU,FRI"
  
  # Data retention
  raw_data_retention_days: 365
  processed_data_retention_days: 1095
  log_retention_days: 30
  
  # Performance thresholds
  max_execution_time_minutes: 30
  alert_threshold_failures: 3
  data_freshness_threshold_minutes: 60
```

## Monitoring and Observability

### Health Check Endpoints
```
/health/airflow     - Airflow scheduler and webserver status
/health/airbyte     - Airbyte connector and sync status  
/health/mlflow      - MLflow tracking server status
/health/knime       - KNIME Analytics Platform status
/health/mysql       - Database connectivity status
/health/redis       - Redis broker status
```

### Key Performance Indicators (KPIs)
- **Data Pipeline Health**: Success rate, execution time, data freshness
- **Model Performance**: Accuracy, precision, prediction latency
- **Trading Performance**: Returns, Sharpe ratio, maximum drawdown
- **System Performance**: Resource utilization, error rates, uptime

### Alerting Rules
```yaml
Critical Alerts:
  - Data pipeline failure > 3 consecutive runs
  - Model accuracy degradation > 10%
  - Trading loss > daily risk limit
  - System resource utilization > 90%

Warning Alerts:
  - Data delay > 1 hour
  - Workflow execution time > 150% of baseline
  - Model retraining required
  - Disk space > 80% utilized
```

## Development Guidelines

### 1. Workflow Development
- **Naming Conventions**: Use descriptive names with environment prefixes
- **Documentation**: Comprehensive README and inline documentation
- **Testing**: Unit tests for individual components, integration tests for workflows
- **Version Control**: Git-based workflow versioning with semantic versioning

### 2. Code Organization
```
workflows/{environment}/
├── dags/              # Workflow definitions
├── config/            # Configuration files
├── scripts/           # Utility scripts
├── tests/            # Test files
├── docs/             # Documentation
└── README.md         # Environment-specific documentation
```

### 3. Best Practices
- **Idempotency**: Ensure workflows can be safely re-run
- **Error Handling**: Implement comprehensive error handling and recovery
- **Logging**: Structured logging with appropriate log levels
- **Security**: Secure credential management and access controls

### 4. Performance Optimization
- **Resource Management**: Optimize memory and CPU usage
- **Parallel Processing**: Leverage parallel execution where appropriate
- **Caching**: Implement intelligent caching strategies
- **Data Optimization**: Efficient data processing and storage patterns

## Troubleshooting

### Common Issues
1. **Service Startup Failures**: Check Docker container status and logs
2. **Database Connection Issues**: Verify MySQL connectivity and credentials  
3. **Memory Issues**: Monitor resource usage and adjust container limits
4. **Workflow Failures**: Check Airflow UI for task logs and error details

### Debugging Tools
- **Airflow UI**: Task logs, DAG visualization, execution history
- **Docker Logs**: Container-level logging and debugging
- **MLflow UI**: Experiment tracking, model performance analysis
- **System Monitoring**: Resource utilization, network connectivity

### Recovery Procedures
```bash
# Restart individual services
docker-compose restart airflow-webserver
docker-compose restart mlflow
docker-compose restart airbyte-webapp

# Reset workflow state
airflow dags state bentleybot_dag 2025-11-21 --subdir /opt/airflow/dags

# Clear workflow history
airflow dags delete bentleybot_dag
```

## Future Enhancements

### Planned Features
- **Kubernetes Deployment**: Container orchestration for production scaling
- **Advanced ML Pipeline**: AutoML integration and hyperparameter optimization  
- **Real-time Analytics**: Stream processing with Apache Kafka integration
- **Advanced Monitoring**: Custom dashboards and predictive alerting

### Scalability Improvements
- **Distributed Computing**: Spark integration for large-scale data processing
- **Multi-Environment Support**: Development, staging, and production environments
- **API Gateway**: Centralized API management and rate limiting
- **Event-Driven Architecture**: Event sourcing and CQRS patterns

## Support and Maintenance

### Documentation
- Individual workflow environment READMEs
- API documentation and integration guides
- Troubleshooting guides and runbooks
- Performance tuning and optimization guides

### Training Resources
- Workflow development tutorials
- Best practices documentation
- Video tutorials and walkthroughs
- Community forums and support channels