# MLflow Experiment Tracking and Model Management
# Configuration and workflows for ML model lifecycle management

## Overview
This folder contains MLflow workflows for experiment tracking, model training, deployment, and lifecycle management for the Bentley Budget Bot's ML capabilities.

## Workflow Structure

### Core ML Workflows
- `mlflow_experiment_dags.py` - Model training, deployment, and experiment management workflows

### Model Types
- **Price Prediction Models**: Stock price forecasting using technical indicators
- **Portfolio Optimization**: Risk-return optimization models
- **Sentiment Analysis**: Market sentiment classification models
- **Anomaly Detection**: Unusual market behavior detection

## MLflow Configuration

### Server Setup
```yaml
# MLflow Server Configuration
mlflow:
  tracking_uri: "http://localhost:5000"
  backend_store: "sqlite:///mlflow/mlflow.db"
  artifact_store: "/mlflow/artifacts"
  serve_artifacts: true
```

### Experiment Organization
```
BentleyBot Experiments/
├── Financial-Models/
│   ├── Price-Prediction/
│   ├── Portfolio-Optimization/
│   └── Risk-Assessment/
├── Trading-Strategies/
│   ├── Technical-Analysis/
│   ├── Sentiment-Based/
│   └── Hybrid-Strategies/
└── Data-Quality/
    ├── Anomaly-Detection/
    └── Validation-Models/
```

## Model Development Pipeline

### 1. Data Preparation
```python
# Example data preparation workflow
def prepare_training_data():
    # Load from MySQL
    engine = create_engine(MYSQL_URL)
    
    # Feature engineering
    features = create_technical_indicators(raw_data)
    target = calculate_returns(raw_data)
    
    # Data validation
    validate_data_quality(features, target)
    
    return features, target
```

### 2. Model Training
```python
# Model training with MLflow tracking
with mlflow.start_run(experiment_id="price_prediction"):
    # Log parameters
    mlflow.log_param("model_type", "RandomForest")
    mlflow.log_param("n_estimators", 100)
    
    # Train model
    model = train_model(X_train, y_train)
    
    # Evaluate and log metrics
    accuracy = evaluate_model(model, X_test, y_test)
    mlflow.log_metric("accuracy", accuracy)
    
    # Log model artifact
    mlflow.sklearn.log_model(model, "model")
```

### 3. Model Deployment
```python
# Model registration and deployment
model_uri = f"runs:/{run_id}/model"
model_version = mlflow.register_model(model_uri, "PricePrediction")

# Promote to staging
client = mlflow.MlflowClient()
client.transition_model_version_stage(
    name="PricePrediction",
    version=model_version.version,
    stage="Staging"
)
```

## Experiment Tracking

### Key Metrics to Track
- **Model Performance**: Accuracy, precision, recall, F1-score
- **Financial Metrics**: Sharpe ratio, maximum drawdown, returns
- **Risk Metrics**: Value at Risk (VaR), volatility, beta
- **Operational Metrics**: Training time, inference latency, memory usage

### Parameter Tracking
```python
# Standard parameters to log
mlflow.log_param("data_start_date", start_date)
mlflow.log_param("data_end_date", end_date)
mlflow.log_param("feature_set", feature_columns)
mlflow.log_param("target_variable", target_name)
mlflow.log_param("train_test_split", 0.8)
mlflow.log_param("random_seed", 42)
```

### Artifact Management
```python
# Artifacts to save
mlflow.log_artifact("feature_importance.png")
mlflow.log_artifact("model_performance.json")
mlflow.log_artifact("prediction_results.csv")
mlflow.log_artifact("training_config.yaml")
```

## Model Registry

### Model Lifecycle Stages
1. **None**: Initial model version
2. **Staging**: Model ready for testing
3. **Production**: Model deployed for live trading
4. **Archived**: Deprecated model versions

### Model Versioning Strategy
```
Model Name: BentleyBot-PricePrediction
├── Version 1 (Production) - Random Forest Baseline
├── Version 2 (Staging) - XGBoost Improvement  
└── Version 3 (None) - Neural Network Experiment
```

## Model Serving and Inference

### Batch Inference
```python
# Load production model for batch predictions
model = mlflow.pyfunc.load_model("models:/PricePrediction/Production")

# Generate predictions for portfolio
predictions = model.predict(market_data)

# Store results
save_predictions(predictions, timestamp=datetime.now())
```

### Real-time Inference
```python
# Model serving endpoint
app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    model = mlflow.pyfunc.load_model("models:/PricePrediction/Production")
    prediction = model.predict(pd.DataFrame(data))
    return jsonify({"prediction": prediction.tolist()})
```

## Model Monitoring

### Performance Monitoring
- **Data Drift**: Monitor feature distributions over time
- **Prediction Drift**: Track prediction patterns and confidence
- **Model Degradation**: Monitor accuracy metrics in production
- **Business Impact**: Track trading performance and profitability

### Automated Alerts
```python
# Example monitoring checks
def check_model_performance():
    recent_predictions = load_recent_predictions()
    recent_actuals = load_recent_actuals()
    
    current_accuracy = calculate_accuracy(recent_predictions, recent_actuals)
    baseline_accuracy = get_baseline_accuracy()
    
    if current_accuracy < baseline_accuracy * 0.9:  # 10% degradation threshold
        send_alert("Model performance degraded")
        trigger_retraining()
```

## A/B Testing Framework

### Experiment Design
```python
# A/B test setup for model comparison
def setup_ab_test(control_model, treatment_model, traffic_split=0.5):
    with mlflow.start_run(experiment_id="ab_test"):
        mlflow.log_param("control_model", control_model)
        mlflow.log_param("treatment_model", treatment_model)
        mlflow.log_param("traffic_split", traffic_split)
        
        # Implement random assignment logic
        return experiment_config
```

### Statistical Analysis
```python
# Analyze A/B test results
def analyze_ab_test(experiment_id):
    results = mlflow.search_runs(experiment_ids=[experiment_id])
    
    # Statistical significance testing
    p_value = statistical_test(control_metrics, treatment_metrics)
    
    mlflow.log_metric("p_value", p_value)
    mlflow.log_metric("statistical_significance", p_value < 0.05)
```

## Data Science Best Practices

### 1. Reproducibility
- Use fixed random seeds
- Version control for code and data
- Environment specification (requirements.txt)
- Docker containers for consistent environments

### 2. Model Validation
- Cross-validation for robust performance estimates
- Out-of-time validation for financial models
- Walk-forward analysis for time series
- Stress testing under different market conditions

### 3. Feature Engineering
- Technical indicators (RSI, MACD, Bollinger Bands)
- Fundamental analysis ratios
- Market sentiment features
- Economic indicators and calendar events

### 4. Risk Management
- Position sizing based on model confidence
- Stop-loss and take-profit mechanisms
- Portfolio diversification constraints
- Real-time risk monitoring

## Integration Points

### Airflow Integration
- Scheduled model retraining
- Automated model deployment
- Performance monitoring workflows
- Data pipeline dependencies

### Trading System Integration
- Real-time prediction serving
- Signal generation and filtering
- Risk management integration
- Performance attribution analysis

### Monitoring and Alerting
- Model performance dashboards
- Automated retraining triggers
- Performance degradation alerts
- Business impact tracking

## Troubleshooting

### Common Issues
1. **Model Training Failures**: Check data quality and feature engineering
2. **Serving Latency**: Optimize model size and inference code
3. **Memory Issues**: Use model compression and efficient data loading
4. **Version Conflicts**: Ensure consistent MLflow and model dependencies

### Debugging Tools
- MLflow UI for experiment analysis
- Model comparison utilities
- Performance profiling tools
- Data quality validation reports