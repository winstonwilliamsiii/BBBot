# MLflow Experiment Tracking and Model Management DAGs
# This folder contains DAGs for MLflow experiment tracking, model deployment, and ML pipelines

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import mlflow
import mlflow.sklearn
import pandas as pd
import logging
from sqlalchemy import create_engine

# MLflow Configuration
MLFLOW_TRACKING_URI = "http://localhost:5000"
MYSQL_URL = "mysql+pymysql://airflow:airflow@mysql:3306/mansa_bot"

default_args = {
    'owner': 'bentley-budget-bot',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 21),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=3),
}

# === Model Training Pipeline DAG ===
dag_model_training = DAG(
    'mlflow_model_training',
    default_args=default_args,
    description='Train and track ML models for financial predictions',
    schedule_interval='@daily',
    catchup=False,
    tags=['mlflow', 'machine-learning', 'training']
)

def setup_mlflow():
    """Initialize MLflow tracking"""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment("BentleyBot-Financial-Models")
    logging.info(f"MLflow tracking URI set to: {MLFLOW_TRACKING_URI}")

def load_training_data():
    """Load data for model training"""
    engine = create_engine(MYSQL_URL)
    
    # Example: Load financial data for training
    query = """
    SELECT 
        timestamp,
        open_price,
        high_price,
        low_price,
        close_price,
        volume,
        rsi,
        macd
    FROM financial_indicators 
    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    ORDER BY timestamp ASC
    """
    
    df = pd.read_sql(query, engine)
    engine.dispose()
    
    # Save to temporary location for next task
    df.to_csv('/tmp/training_data.csv', index=False)
    logging.info(f"Loaded {len(df)} rows of training data")
    return len(df)

def train_price_prediction_model():
    """Train a price prediction model"""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    with mlflow.start_run(run_name="price_prediction_model") as run:
        # Load data
        df = pd.read_csv('/tmp/training_data.csv')
        
        # Simple feature engineering
        df['price_change'] = df['close_price'].pct_change()
        df['volatility'] = df['close_price'].rolling(window=5).std()
        df = df.dropna()
        
        # Prepare features and target
        features = ['rsi', 'macd', 'volatility', 'volume']
        target = 'price_change'
        
        X = df[features]
        y = df[target]
        
        # Simple model training (example)
        from sklearn.ensemble import RandomForestRegressor
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_squared_error, r2_score
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Log parameters
        mlflow.log_param("model_type", "RandomForestRegressor")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("features", features)
        mlflow.log_param("training_samples", len(X_train))
        
        # Log metrics
        mlflow.log_metric("mse", mse)
        mlflow.log_metric("r2_score", r2)
        mlflow.log_metric("rmse", mse ** 0.5)
        
        # Log model
        mlflow.sklearn.log_model(model, "price_prediction_model")
        
        # Log artifacts
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 6))
        plt.scatter(y_test, y_pred, alpha=0.5)
        plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
        plt.xlabel('Actual Price Change')
        plt.ylabel('Predicted Price Change')
        plt.title('Price Prediction Model Performance')
        plt.savefig('/tmp/prediction_performance.png')
        mlflow.log_artifact('/tmp/prediction_performance.png')
        
        logging.info(f"Model training completed. Run ID: {run.info.run_id}")
        logging.info(f"Model Performance - MSE: {mse:.6f}, R²: {r2:.4f}")

# Tasks
setup_mlflow_task = PythonOperator(
    task_id='setup_mlflow',
    python_callable=setup_mlflow,
    dag=dag_model_training
)

load_data_task = PythonOperator(
    task_id='load_training_data',
    python_callable=load_training_data,
    dag=dag_model_training
)

train_model_task = PythonOperator(
    task_id='train_price_prediction_model',
    python_callable=train_price_prediction_model,
    dag=dag_model_training
)

# Dependencies
setup_mlflow_task >> load_data_task >> train_model_task

# === Model Deployment DAG ===
dag_model_deployment = DAG(
    'mlflow_model_deployment',
    default_args=default_args,
    description='Deploy and serve ML models',
    schedule_interval=None,  # Manual trigger
    catchup=False,
    tags=['mlflow', 'deployment', 'serving']
)

def register_best_model():
    """Register the best performing model"""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    # Get the best model from the experiment
    experiment = mlflow.get_experiment_by_name("BentleyBot-Financial-Models")
    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["metrics.r2_score DESC"],
        max_results=1
    )
    
    if len(runs) > 0:
        best_run = runs.iloc[0]
        model_uri = f"runs:/{best_run.run_id}/price_prediction_model"
        
        # Register model
        model_version = mlflow.register_model(
            model_uri=model_uri,
            name="BentleyBot-PricePrediction"
        )
        
        # Transition to staging
        client = mlflow.tracking.MlflowClient()
        client.transition_model_version_stage(
            name="BentleyBot-PricePrediction",
            version=model_version.version,
            stage="Staging"
        )
        
        logging.info(f"Model registered and transitioned to Staging: Version {model_version.version}")
    else:
        logging.warning("No models found to register")

register_model_task = PythonOperator(
    task_id='register_best_model',
    python_callable=register_best_model,
    dag=dag_model_deployment
)

# === Experiment Cleanup DAG ===
dag_cleanup = DAG(
    'mlflow_experiment_cleanup',
    default_args=default_args,
    description='Clean up old MLflow experiments and artifacts',
    schedule_interval='@weekly',
    catchup=False,
    tags=['mlflow', 'maintenance', 'cleanup']
)

def cleanup_old_experiments():
    """Clean up experiments older than 30 days"""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    
    # Get old runs
    cutoff_date = datetime.now() - timedelta(days=30)
    cutoff_timestamp = int(cutoff_date.timestamp() * 1000)
    
    experiment = mlflow.get_experiment_by_name("BentleyBot-Financial-Models")
    old_runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string=f"attribute.start_time < {cutoff_timestamp}",
        run_view_type=mlflow.entities.ViewType.ALL
    )
    
    client = mlflow.tracking.MlflowClient()
    
    for _, run in old_runs.iterrows():
        run_id = run.run_id
        if run.lifecycle_stage != "deleted":
            client.delete_run(run_id)
            logging.info(f"Deleted old run: {run_id}")
    
    logging.info(f"Cleanup completed. Processed {len(old_runs)} old runs")

cleanup_task = PythonOperator(
    task_id='cleanup_old_experiments',
    python_callable=cleanup_old_experiments,
    dag=dag_cleanup
)