# KNIME Analytics Workflows
# Configuration and workflows for KNIME-based data analytics and modeling

## Overview
This folder contains KNIME workflow integration for advanced analytics, visual programming, and enterprise data science capabilities within the Bentley Budget Bot ecosystem.

## Workflow Structure

### Core Analytics Workflows
- `knime_workflow_dags.py` - KNIME workflow execution, monitoring, and integration DAGs

### KNIME Workflow Categories
- **Financial Analytics**: Portfolio analysis, risk assessment, performance attribution
- **Market Analysis**: Technical analysis, pattern recognition, trend detection  
- **Data Processing**: ETL workflows, data quality checks, feature engineering
- **Reporting**: Automated report generation, dashboard data preparation

## KNIME Configuration

### KNIME Analytics Platform Setup
```yaml
# KNIME Configuration
knime:
  executor_path: "/opt/knime/knime"
  workflows_path: "/app/knime_workflows" 
  workspace_path: "/app/knime_workspace"
  temp_path: "/tmp/knime_temp"
```

### KNIME Server Configuration (Enterprise)
```yaml
# KNIME Server Setup
knime_server:
  url: "http://localhost:8080/knime"
  auth:
    username: "${KNIME_SERVER_USER}"
    password: "${KNIME_SERVER_PASSWORD}"
  repository: "bentley-bot-workflows"
```

## Workflow Organization

### Directory Structure
```
knime_workflows/
├── financial_analytics/
│   ├── portfolio_risk_analysis/
│   ├── performance_attribution/
│   └── stress_testing/
├── market_analysis/
│   ├── technical_indicators/
│   ├── pattern_recognition/
│   └── sentiment_analysis/
├── data_processing/
│   ├── data_quality_checks/
│   ├── feature_engineering/
│   └── data_transformation/
└── reporting/
    ├── daily_reports/
    ├── weekly_summaries/
    └── monthly_analytics/
```

## Key Workflow Implementations

### 1. Portfolio Risk Analysis
```
Input: Portfolio holdings, market data, risk parameters
Processing: VaR calculation, stress testing, correlation analysis
Output: Risk metrics, scenario analysis, risk reports
```

**Workflow Features:**
- Monte Carlo simulation for VaR calculation
- Historical simulation for backtesting
- Parametric risk models (GARCH, etc.)
- Correlation and covariance matrix analysis
- Tail risk and extreme value analysis

### 2. Technical Analysis Suite
```
Input: OHLCV market data, technical parameters
Processing: Indicator calculation, signal generation, pattern detection
Output: Trading signals, technical indicators, chart patterns
```

**Implemented Indicators:**
- Moving averages (SMA, EMA, VWMA)
- Momentum indicators (RSI, MACD, Stochastic)
- Volatility indicators (Bollinger Bands, ATR)
- Volume indicators (OBV, Volume Profile)
- Custom composite indicators

### 3. Market Sentiment Analysis
```
Input: News articles, social media data, market data
Processing: Text analysis, sentiment scoring, impact assessment
Output: Sentiment scores, market impact predictions, alerts
```

**Sentiment Processing:**
- Text preprocessing and cleaning
- Named entity recognition (financial entities)
- Sentiment classification (positive/negative/neutral)
- Impact correlation with market movements
- Real-time sentiment monitoring

### 4. Data Quality Framework
```
Input: Raw financial data from multiple sources
Processing: Validation rules, anomaly detection, cleansing
Output: Quality reports, cleaned data, exception alerts
```

**Quality Checks:**
- Data completeness and consistency
- Range and format validation
- Cross-source data reconciliation
- Temporal consistency checks
- Outlier detection and handling

## Workflow Execution Patterns

### Scheduled Execution
```python
# Daily risk analysis workflow
execute_knime_workflow(
    workflow_name="Portfolio Risk Analysis",
    workflow_path="/knime_workflows/portfolio_risk_analysis",
    schedule="0 6 * * 1-5",  # 6 AM weekdays
    parameters={
        "risk_horizon": "1d",
        "confidence_level": "0.95",
        "portfolio_date": "{{ ds }}"
    }
)
```

### Event-Driven Execution
```python
# Market volatility spike trigger
def check_volatility_trigger():
    current_vix = get_current_vix()
    if current_vix > volatility_threshold:
        execute_knime_workflow(
            workflow_name="Stress Testing",
            workflow_path="/knime_workflows/stress_testing",
            parameters={"stress_scenario": "high_volatility"}
        )
```

### Batch Processing
```python
# Monthly portfolio rebalancing analysis
execute_monthly_workflows = [
    "portfolio_optimization",
    "performance_attribution", 
    "risk_decomposition",
    "regulatory_reporting"
]
```

## Integration with KNIME Server

### Workflow Deployment
```python
# Deploy workflow to KNIME Server
def deploy_workflow_to_server(workflow_path, server_location):
    # Upload workflow to repository
    upload_workflow(workflow_path, server_location)
    
    # Configure execution settings
    configure_execution_profile(server_location, {
        "memory_limit": "4GB",
        "timeout": "30m",
        "priority": "normal"
    })
    
    # Set up monitoring
    enable_workflow_monitoring(server_location)
```

### Remote Execution
```python
# Execute workflow on KNIME Server
def execute_server_workflow(workflow_id, parameters):
    response = requests.post(
        f"{KNIME_SERVER_URL}/rest/v4/repository/{workflow_id}:execute",
        json={
            "async": False,
            "timeout": 1800,
            "workflow-variables": parameters
        }
    )
    return response.json()
```

## Data Flow Integration

### Input Data Sources
- **MySQL Database**: Core financial data repository
- **Airbyte Synced Data**: External API data feeds
- **File Uploads**: Manual data imports (CSV, Excel)
- **Real-time Feeds**: Live market data streams

### Output Destinations
- **MySQL Tables**: Processed analytics results
- **File Exports**: Reports and data exports
- **MLflow Artifacts**: Model inputs and validation data
- **Dashboard APIs**: Real-time analytics for UI

### Data Validation Pipeline
```
Raw Data → KNIME Quality Checks → Validated Data → Analytics Processing → Results Validation → Output Storage
```

## Monitoring and Performance

### Workflow Health Monitoring
```python
# Monitor workflow execution health
def monitor_workflow_health():
    metrics = {
        "total_workflows": count_active_workflows(),
        "successful_executions": count_successful_runs(last_24h),
        "failed_executions": count_failed_runs(last_24h), 
        "average_execution_time": calculate_avg_runtime(),
        "resource_utilization": get_resource_usage()
    }
    
    # Alert on anomalies
    if metrics["failed_executions"] > failure_threshold:
        send_alert("High workflow failure rate detected")
```

### Performance Optimization
- **Memory Management**: Optimize node memory settings
- **Parallel Execution**: Configure parallel processing
- **Data Chunking**: Process large datasets in chunks
- **Cache Management**: Optimize intermediate data caching

### Resource Monitoring
```python
# Track resource usage
def track_resource_usage():
    return {
        "cpu_usage": get_cpu_utilization(),
        "memory_usage": get_memory_utilization(),
        "disk_io": get_disk_io_stats(),
        "network_io": get_network_io_stats(),
        "execution_queue": get_queue_length()
    }
```

## Error Handling and Recovery

### Automatic Recovery
```python
# Workflow failure recovery
def handle_workflow_failure(workflow_id, error_details):
    if is_recoverable_error(error_details):
        # Retry with adjusted parameters
        retry_workflow(workflow_id, retry_params)
    else:
        # Log error and send alert
        log_critical_error(workflow_id, error_details)
        notify_administrators(error_details)
```

### Data Validation Recovery
- **Fallback Data Sources**: Use alternative data when primary fails
- **Partial Processing**: Continue with available data subsets
- **Manual Intervention**: Queue workflows for manual review
- **Graceful Degradation**: Reduce analysis scope when resources limited

## Best Practices

### 1. Workflow Design
- **Modular Components**: Use reusable workflow components
- **Clear Documentation**: Document each workflow's purpose and inputs
- **Version Control**: Maintain workflow versions and change logs
- **Testing**: Implement unit tests for workflow components

### 2. Performance Optimization
- **Efficient Nodes**: Use appropriate node types for data operations
- **Memory Management**: Configure memory limits appropriately
- **Parallel Processing**: Leverage parallel execution where possible
- **Data Streaming**: Use streaming for large datasets

### 3. Maintenance and Operations
- **Regular Updates**: Keep KNIME platform and extensions updated
- **Backup Strategies**: Regular workflow and data backups
- **Documentation**: Maintain operational runbooks
- **Training**: Ensure team familiarity with KNIME operations

### 4. Security and Governance
- **Access Controls**: Implement proper user permissions
- **Data Privacy**: Ensure compliance with data protection regulations
- **Audit Trails**: Maintain execution logs and audit trails
- **Change Management**: Controlled workflow deployment processes

## Integration Points

### Airflow Orchestration
- Trigger KNIME workflows from Airflow DAGs
- Handle workflow dependencies and scheduling
- Monitor workflow status and handle failures
- Coordinate with other system components

### MLflow Integration
- Use KNIME for feature engineering in ML pipelines
- Generate training datasets for MLflow experiments
- Validate model outputs using KNIME workflows
- Create model performance reports

### Real-time Analytics
- Stream processing for real-time market analysis
- Event-driven workflow triggers
- Real-time dashboard data preparation
- Alert and notification systems

## Troubleshooting

### Common Issues
1. **Memory Errors**: Increase JVM heap size, optimize data handling
2. **Workflow Timeouts**: Adjust timeout settings, optimize performance
3. **Data Format Issues**: Implement robust data validation and conversion
4. **Node Compatibility**: Ensure extension compatibility with KNIME version

### Debugging Strategies
- Enable detailed logging in workflow execution
- Use KNIME's built-in debugging tools
- Implement data quality checkpoints throughout workflows
- Monitor system resources during execution