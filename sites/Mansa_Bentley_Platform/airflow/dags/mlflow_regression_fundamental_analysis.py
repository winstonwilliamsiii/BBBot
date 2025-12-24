"""
MLFlow Regression Fundamental Analysis DAG
Trains regression models on fundamental ratios to predict ROI
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import sys
import os

# Add bbbot1_pipeline to Python path
sys.path.insert(0, '/opt/airflow')

# Import required modules
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

try:
    from bbbot1_pipeline.mlflow_config import get_mlflow_tracking_uri
    from bbbot1_pipeline.mlflow_tracker import get_tracker
    from bbbot1_pipeline.db import get_mysql_connection
    from bbbot1_pipeline import load_tickers_config
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False

# DAG configuration
default_args = {
    'owner': 'bentleybot',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def fetch_fundamental_data(**context):
    """
    Task 1: Fetch fundamental data from MySQL database
    """
    print("="*80)
    print("TASK 1: Fetching Fundamental Data")
    print("="*80)
    
    if not IMPORTS_AVAILABLE:
        print("⚠️ Required imports not available")
        return None
    
    try:
        conn = get_mysql_connection()
        
        # Query fundamental data
        query = """
        SELECT 
            ticker,
            report_date,
            pe_ratio,
            market_cap,
            eps,
            revenue,
            net_income,
            total_assets,
            total_liabilities
        FROM stock_fundamentals
        WHERE pe_ratio IS NOT NULL
        ORDER BY report_date DESC
        LIMIT 1000
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"✓ Fetched {len(df)} fundamental records")
        print(f"  Tickers: {df['ticker'].nunique()}")
        print(f"  Date range: {df['report_date'].min()} to {df['report_date'].max()}")
        
        # Push to XCom
        context['task_instance'].xcom_push(key='fundamentals_df', value=df.to_json())
        
        return len(df)
        
    except Exception as e:
        print(f"✗ Error fetching fundamental data: {e}")
        raise


def calculate_derived_ratios(**context):
    """
    Task 2: Calculate derived financial ratios
    """
    print("="*80)
    print("TASK 2: Calculating Derived Ratios")
    print("="*80)
    
    # Pull data from XCom
    ti = context['task_instance']
    df_json = ti.xcom_pull(task_ids='fetch_fundamental_data', key='fundamentals_df')
    
    if not df_json:
        print("⚠️ No fundamental data available")
        return None
    
    df = pd.read_json(df_json)
    
    # Calculate additional ratios
    df['pb_ratio'] = df['market_cap'] / df['total_assets']
    df['debt_to_equity'] = df['total_liabilities'] / (df['total_assets'] - df['total_liabilities'])
    df['profit_margin'] = df['net_income'] / df['revenue']
    df['roa'] = df['net_income'] / df['total_assets']
    df['roe'] = df['net_income'] / (df['total_assets'] - df['total_liabilities'])
    
    # Calculate target variable (ROI) - simplified as profit margin for this example
    df['roi'] = df['profit_margin']
    
    # Drop rows with NaN in key columns
    df = df.dropna(subset=['pe_ratio', 'pb_ratio', 'roa', 'roe', 'roi'])
    
    print(f"✓ Calculated derived ratios for {len(df)} records")
    print(f"  Available features: pe_ratio, pb_ratio, debt_to_equity, roa, roe")
    print(f"  Target variable: roi")
    
    # Push to XCom
    ti.xcom_push(key='ratios_df', value=df.to_json())
    
    return len(df)


def train_linear_regression_model(**context):
    """
    Task 3: Train Linear Regression model
    """
    print("="*80)
    print("TASK 3: Training Linear Regression Model")
    print("="*80)
    
    # Pull data from XCom
    ti = context['task_instance']
    df_json = ti.xcom_pull(task_ids='calculate_derived_ratios', key='ratios_df')
    
    if not df_json:
        print("⚠️ No ratio data available")
        return None
    
    df = pd.read_json(df_json)
    
    # Prepare features and target
    feature_cols = ['pe_ratio', 'pb_ratio', 'roa', 'roe', 'debt_to_equity']
    X = df[feature_cols].fillna(0)
    y = df['roi'].fillna(0)
    
    if len(X) < 10:
        print("⚠️ Insufficient data for training")
        return None
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Set MLFlow tracking URI
    if IMPORTS_AVAILABLE:
        mlflow.set_tracking_uri(get_mlflow_tracking_uri())
    
    # Train model
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    r2 = r2_score(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    print(f"✓ Model trained on {len(X_train)} samples")
    print(f"  R² Score: {r2:.4f}")
    print(f"  MSE: {mse:.4f}")
    print(f"  MAE: {mae:.4f}")
    
    # Log to MLFlow
    with mlflow.start_run(run_name="LinearRegression_ROI_Prediction"):
        # Log parameters
        mlflow.log_param("model_type", "LinearRegression")
        mlflow.log_param("features", feature_cols)
        mlflow.log_param("train_size", len(X_train))
        mlflow.log_param("test_size", len(X_test))
        
        # Log metrics
        mlflow.log_metric("r2_score", r2)
        mlflow.log_metric("mse", mse)
        mlflow.log_metric("mae", mae)
        
        # Log model
        mlflow.sklearn.log_model(model, artifact_path="roi_model")
        
        # Save predictions
        pred_df = pd.DataFrame({
            "y_true": y_test.values,
            "y_pred": y_pred
        })
        pred_df.to_csv("/tmp/roi_predictions_linear.csv", index=False)
        mlflow.log_artifact("/tmp/roi_predictions_linear.csv")
    
    print("✓ Model logged to MLFlow")
    
    return r2


def train_random_forest_model(**context):
    """
    Task 4: Train Random Forest model
    """
    print("="*80)
    print("TASK 4: Training Random Forest Model")
    print("="*80)
    
    # Pull data from XCom
    ti = context['task_instance']
    df_json = ti.xcom_pull(task_ids='calculate_derived_ratios', key='ratios_df')
    
    if not df_json:
        print("⚠️ No ratio data available")
        return None
    
    df = pd.read_json(df_json)
    
    # Prepare features and target
    feature_cols = ['pe_ratio', 'pb_ratio', 'roa', 'roe', 'debt_to_equity']
    X = df[feature_cols].fillna(0)
    y = df['roi'].fillna(0)
    
    if len(X) < 10:
        print("⚠️ Insufficient data for training")
        return None
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Set MLFlow tracking URI
    if IMPORTS_AVAILABLE:
        mlflow.set_tracking_uri(get_mlflow_tracking_uri())
    
    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    r2 = r2_score(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    print(f"✓ Model trained on {len(X_train)} samples")
    print(f"  R² Score: {r2:.4f}")
    print(f"  MSE: {mse:.4f}")
    print(f"  MAE: {mae:.4f}")
    
    # Log to MLFlow
    with mlflow.start_run(run_name="RandomForest_ROI_Prediction"):
        # Log parameters
        mlflow.log_param("model_type", "RandomForestRegressor")
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("features", feature_cols)
        mlflow.log_param("train_size", len(X_train))
        mlflow.log_param("test_size", len(X_test))
        
        # Log metrics
        mlflow.log_metric("r2_score", r2)
        mlflow.log_metric("mse", mse)
        mlflow.log_metric("mae", mae)
        
        # Log feature importance
        feature_importance = dict(zip(feature_cols, model.feature_importances_))
        for feature, importance in feature_importance.items():
            mlflow.log_metric(f"importance_{feature}", importance)
        
        # Log model
        mlflow.sklearn.log_model(model, artifact_path="roi_model")
        
        # Save predictions
        pred_df = pd.DataFrame({
            "y_true": y_test.values,
            "y_pred": y_pred
        })
        pred_df.to_csv("/tmp/roi_predictions_rf.csv", index=False)
        mlflow.log_artifact("/tmp/roi_predictions_rf.csv")
    
    print("✓ Model logged to MLFlow")
    
    return r2


# Create the DAG
with DAG(
    dag_id='mlflow_regression_fundamental_analysis',
    default_args=default_args,
    description='Train regression models on fundamental ratios with MLFlow tracking',
    schedule_interval='0 20 * * 1-5',  # Run at 8 PM on weekdays
    start_date=days_ago(1),
    catchup=False,
    tags=['mlflow', 'regression', 'fundamentals', 'ml'],
) as dag:
    
    # Task 1: Fetch fundamental data
    task_fetch_data = PythonOperator(
        task_id='fetch_fundamental_data',
        python_callable=fetch_fundamental_data,
        provide_context=True,
    )
    
    # Task 2: Calculate derived ratios
    task_calculate_ratios = PythonOperator(
        task_id='calculate_derived_ratios',
        python_callable=calculate_derived_ratios,
        provide_context=True,
    )
    
    # Task 3: Train Linear Regression
    task_train_linear = PythonOperator(
        task_id='train_linear_regression',
        python_callable=train_linear_regression_model,
        provide_context=True,
    )
    
    # Task 4: Train Random Forest
    task_train_rf = PythonOperator(
        task_id='train_random_forest',
        python_callable=train_random_forest_model,
        provide_context=True,
    )
    
    # Define task dependencies
    task_fetch_data >> task_calculate_ratios >> [task_train_linear, task_train_rf]


# DAG Documentation
__doc__ = """
# MLFlow Regression Fundamental Analysis DAG

## Purpose
Trains machine learning regression models to predict ROI from fundamental financial ratios.

## Schedule
- **Frequency**: Daily at 8 PM (weekdays only)
- **Reason**: After market close and after fundamental data is updated

## Task Sequence
1. **fetch_fundamental_data**: Query MySQL for fundamental ratios
2. **calculate_derived_ratios**: Compute additional financial ratios
3. **train_linear_regression**: Train Linear Regression model (parallel)
4. **train_random_forest**: Train Random Forest model (parallel)

## Features Used
- P/E Ratio
- Price-to-Book Ratio
- Return on Assets (ROA)
- Return on Equity (ROE)
- Debt-to-Equity Ratio

## Target Variable
- ROI (Return on Investment) / Profit Margin

## MLFlow Integration
- All models logged to MySQL backend (mlflow_db)
- Tracks: parameters, metrics (R², MSE, MAE), models, predictions
- Connection: 127.0.0.1:3306/mlflow_db

## Manual Trigger
```bash
docker exec bentley-airflow-webserver airflow dags trigger mlflow_regression_fundamental_analysis
```

## View Results
Check MLFlow UI or Streamlit "MLFlow Experiments" tab
"""
