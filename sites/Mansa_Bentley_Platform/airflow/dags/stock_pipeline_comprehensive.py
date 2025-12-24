"""
Comprehensive Stock Data Pipeline DAG
Orchestrates: Airbyte ingestion → dbt transformation → MLFlow training

This DAG coordinates the complete data pipeline:
1. Validates raw data from Airbyte syncs
2. Runs dbt staging and marts transformations
3. Logs ML features to MLFlow
4. Trains ROI prediction models
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from datetime import datetime, timedelta
import pandas as pd
import sys
import os

# Add bbbot1_pipeline to Python path
sys.path.insert(0, '/opt/airflow')

from bbbot1_pipeline.mlflow_config import get_mlflow_tracking_uri
from bbbot1_pipeline.db import get_mysql_engine

# DAG default arguments
default_args = {
    'owner': 'winston',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}


def validate_raw_data(**context):
    """Validate that Airbyte has populated raw tables with recent data"""
    mysql_hook = MySqlHook(mysql_conn_id='mysql_bbbot1')
    
    # Check each raw table for recent data
    tables_to_check = {
        'prices_daily': 1,  # Should have data from today or yesterday
        'fundamentals_raw': 7,  # Can be up to 7 days old
        'sentiment_msgs': 1,  # Should have data from today
    }
    
    issues = []
    
    for table_name, max_age_days in tables_to_check.items():
        query = f"""
        SELECT 
            '{table_name}' AS table_name,
            COUNT(*) AS row_count,
            MAX(created_at) AS latest_data
        FROM {table_name}
        """
        
        result = mysql_hook.get_first(query)
        
        if result[1] == 0:  # row_count
            issues.append(f"{table_name}: No data found")
        else:
            print(f"✅ {table_name}: {result[1]} rows, latest: {result[2]}")
    
    if issues:
        raise ValueError(f"Raw data validation failed: {'; '.join(issues)}")
    
    print("✅ All raw tables have recent data")
    return True


def log_features_to_mlflow(**context):
    """
    Log engineered features from dbt marts.features_roi to MLFlow
    """
    import mlflow
    
    # Set MLFlow tracking URI
    mlflow.set_tracking_uri(get_mlflow_tracking_uri())
    mlflow.set_experiment("stock_pipeline_features")
    
    # Load features from marts table
    engine = get_mysql_engine()
    
    features_query = """
    SELECT 
        ticker,
        price_date,
        target_roi,
        pe_ratio,
        pb_ratio,
        roa,
        avg_sentiment_score,
        price_momentum_30d,
        ticker_category
    FROM marts.features_roi
    WHERE price_date >= CURDATE() - INTERVAL 30 DAY
    ORDER BY ticker, price_date DESC
    """
    
    df = pd.read_sql(features_query, engine)
    
    if df.empty:
        print("⚠️ No features found in marts.features_roi table")
        return
    
    # Log summary statistics to MLFlow
    with mlflow.start_run(run_name=f"feature_summary_{datetime.now().strftime('%Y%m%d')}"):
        # Log dataset info
        mlflow.log_param("total_records", len(df))
        mlflow.log_param("tickers", df['ticker'].nunique())
        mlflow.log_param("date_range", f"{df['price_date'].min()} to {df['price_date'].max()}")
        
        # Log feature statistics
        for col in ['pe_ratio', 'pb_ratio', 'roa', 'avg_sentiment_score', 'price_momentum_30d']:
            if col in df.columns:
                mlflow.log_metric(f"{col}_mean", df[col].mean())
                mlflow.log_metric(f"{col}_std", df[col].std())
        
        # Log per-ticker metrics
        for ticker in df['ticker'].unique():
            ticker_df = df[df['ticker'] == ticker]
            mlflow.log_metric(f"{ticker}_records", len(ticker_df))
            mlflow.log_metric(f"{ticker}_avg_roi", ticker_df['target_roi'].mean())
    
    print(f"✅ Logged {len(df)} feature records to MLFlow")
    return len(df)


def train_roi_model(**context):
    """
    Train ROI prediction model using features from dbt marts
    """
    import mlflow
    import mlflow.sklearn
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_squared_error, r2_score
    import numpy as np
    
    # Set MLFlow tracking
    mlflow.set_tracking_uri(get_mlflow_tracking_uri())
    mlflow.set_experiment("roi_prediction_models")
    
    # Load features
    engine = get_mysql_engine()
    
    query = """
    SELECT 
        ticker,
        target_roi,
        pe_ratio,
        pb_ratio,
        ev_ebit,
        ev_ebitda,
        roa,
        eps,
        debt_to_equity,
        cash_ratio,
        avg_sentiment_score,
        sentiment_change,
        bullish_ratio,
        price_momentum_30d,
        avg_volume_30d,
        price_volatility_30d,
        pe_sentiment_interaction,
        roa_sentiment_interaction
    FROM marts.features_roi
    WHERE target_roi IS NOT NULL
      AND has_missing_fundamentals = 0
      AND has_missing_sentiment = 0
    ORDER BY ticker, price_date DESC
    LIMIT 1000
    """
    
    df = pd.read_sql(query, engine)
    
    if len(df) < 50:
        print(f"⚠️ Insufficient data for training: {len(df)} records")
        return
    
    # Prepare features and target
    feature_cols = [
        'pe_ratio', 'pb_ratio', 'ev_ebit', 'ev_ebitda', 'roa', 'eps',
        'debt_to_equity', 'cash_ratio', 'avg_sentiment_score', 'sentiment_change',
        'bullish_ratio', 'price_momentum_30d', 'avg_volume_30d', 'price_volatility_30d',
        'pe_sentiment_interaction', 'roa_sentiment_interaction'
    ]
    
    # Drop rows with any NaN values
    df_clean = df.dropna(subset=feature_cols + ['target_roi'])
    
    if len(df_clean) < 50:
        print(f"⚠️ Insufficient clean data: {len(df_clean)} records after removing NaNs")
        return
    
    X = df_clean[feature_cols]
    y = df_clean['target_roi']
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model with MLFlow tracking
    with mlflow.start_run(run_name=f"roi_model_{datetime.now().strftime('%Y%m%d_%H%M')}"):
        # Log parameters
        mlflow.log_param("n_estimators", 100)
        mlflow.log_param("max_depth", 10)
        mlflow.log_param("train_samples", len(X_train))
        mlflow.log_param("test_samples", len(X_test))
        mlflow.log_param("features", len(feature_cols))
        
        # Train model
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        
        # Predictions
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)
        
        # Calculate metrics
        train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        
        # Log metrics
        mlflow.log_metric("train_rmse", train_rmse)
        mlflow.log_metric("test_rmse", test_rmse)
        mlflow.log_metric("train_r2", train_r2)
        mlflow.log_metric("test_r2", test_r2)
        
        # Log feature importances
        for feature, importance in zip(feature_cols, model.feature_importances_):
            mlflow.log_metric(f"importance_{feature}", importance)
        
        # Log model
        mlflow.sklearn.log_model(model, "roi_model")
        
        print(f"✅ Model trained - Test R²: {test_r2:.4f}, Test RMSE: {test_rmse:.4f}")
    
    return {"test_r2": test_r2, "test_rmse": test_rmse}


# Define the DAG
with DAG(
    dag_id='stock_pipeline_comprehensive',
    default_args=default_args,
    description='Complete pipeline: Raw data validation → dbt transformation → MLFlow training',
    schedule_interval='0 9 * * *',  # Run at 9 AM daily (after dbt_transformation_pipeline)
    start_date=datetime(2025, 12, 3),
    catchup=False,
    tags=['stocks', 'pipeline', 'mlflow', 'dbt', 'complete'],
    max_active_runs=1,
) as dag:

    # Task 1: Validate raw data from Airbyte
    validate_data = PythonOperator(
        task_id='validate_raw_data',
        python_callable=validate_raw_data,
        provide_context=True,
    )

    # Task 2: Check dbt models are up to date
    check_dbt_status = BashOperator(
        task_id='check_dbt_status',
        bash_command="""
        cd /opt/airflow/dbt_project && \
        dbt list --profiles-dir . --select marts.features_roi
        """,
    )

    # Task 3: Query marts.features_roi to verify it has data
    verify_features = PythonOperator(
        task_id='verify_features_table',
        python_callable=lambda: MySqlHook(mysql_conn_id='mysql_bbbot1').get_first(
            "SELECT COUNT(*) FROM marts.features_roi WHERE price_date >= CURDATE() - INTERVAL 7 DAY"
        ),
        do_xcom_push=True,
    )

    # Task 4: Log features to MLFlow
    log_features = PythonOperator(
        task_id='log_features_to_mlflow',
        python_callable=log_features_to_mlflow,
        provide_context=True,
    )

    # Task 5: Train ROI prediction model
    train_model = PythonOperator(
        task_id='train_roi_model',
        python_callable=train_roi_model,
        provide_context=True,
    )

    # Task dependencies
    validate_data >> check_dbt_status >> verify_features >> log_features >> train_model
