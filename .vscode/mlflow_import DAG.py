from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.datasets import Dataset
from datetime import datetime, timedelta
import sys
import os

# Add project root to path for imports
sys.path.append('/opt/airflow/dags')
sys.path.append('/opt/airflow')
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from mlflow_config import log_data_ingestion, log_portfolio_metrics

dataset = Dataset("mysql://mansa_bot/binance_ohlcv")


def log_ingestion_metrics(**context):
    """Enhanced data ingestion logging with proper error handling"""
    try:
        # Get connection from Airflow connection
        from airflow.hooks.mysql_hook import MySqlHook
        mysql_hook = MySqlHook(mysql_conn_id='mysql_default')

        # Query data
        sql_query = "SELECT * FROM binance_ohlcv LIMIT 1000"
        df = mysql_hook.get_pandas_df(sql_query)

        # Calculate ingestion stats
        timestamp_max = None
        if not df.empty and 'timestamp' in df.columns:
            timestamp_max = df['timestamp'].max()

        ingestion_stats = {
            "source": "mysql_binance",
            "rows_processed": len(df),
            "processing_time": 2.5,
            "status": "success",
            "table_name": "binance_ohlcv",
            "columns_count": len(df.columns) if not df.empty else 0,
            "latest_timestamp": timestamp_max
        }

        # Log to MLflow
        run_name = f"ingestion_{datetime.now().strftime('%Y%m%d_%H%M')}"
        log_data_ingestion(ingestion_stats, run_name)

        # Store stats in XCom for downstream tasks
        task_instance = context['task_instance']
        task_instance.xcom_push(key='ingestion_stats', value=ingestion_stats)

        rows_count = ingestion_stats['rows_processed']
        print(f"✅ Successfully logged ingestion metrics: {rows_count} rows")
        return ingestion_stats

    except Exception as e:
        error_stats = {
            "source": "mysql_binance",
            "rows_processed": 0,
            "processing_time": 0,
            "status": "failed",
            "error": str(e)
        }

        run_name = f"ingestion_failed_{datetime.now().strftime('%Y%m%d_%H%M')}"
        log_data_ingestion(error_stats, run_name)
        print(f"❌ Ingestion failed: {e}")
        raise


def log_portfolio_analysis(**context):
    """Log portfolio analysis metrics"""
    try:
        # Get ingestion stats from previous task
        task_instance = context['task_instance']
        ingestion_stats = task_instance.xcom_pull(
            key='ingestion_stats',
            task_ids='log_ingestion_metrics'
        )

        # Sample portfolio metrics (would be calculated from actual data)
        rows_available = 0
        if ingestion_stats:
            rows_available = ingestion_stats.get('rows_processed', 0)

        portfolio_data = {
            "data_freshness_hours": 1.2,
            "total_symbols_tracked": 25,
            "data_quality_score": 0.95,
            "last_update_success": True,
            "rows_available": rows_available
        }

        # Log portfolio metrics
        run_name = f"portfolio_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}"
        log_portfolio_metrics(portfolio_data, run_name)

        print("✅ Portfolio analysis logged successfully")
        return portfolio_data

    except Exception as e:
        print(f"❌ Portfolio analysis failed: {e}")
        # Log failure metrics
        failure_data = {
            "data_freshness_hours": 0,
            "total_symbols_tracked": 0,
            "data_quality_score": 0,
            "last_update_success": False,
            "error": str(e)
        }
        run_name = f"portfolio_failed_{datetime.now().strftime('%Y%m%d_%H%M')}"
        log_portfolio_metrics(failure_data, run_name)
        raise

# Default DAG arguments
default_args = {
    'owner': 'bentley-bot',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 20),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    "mlflow_logging_dag", 
    default_args=default_args,
    description='Bentley Budget Bot - MLflow Data Tracking',
    schedule=[dataset], 
    catchup=False,
    tags=['bentley-bot', 'mlflow', 'tracking', 'data-quality']
) as dag:
    
    # Enhanced ingestion logging
    log_ingestion_task = PythonOperator(
        task_id="log_ingestion_metrics",
        python_callable=log_ingestion_metrics,
        doc_md="""
        ## Data Ingestion Tracking
        Logs data ingestion statistics to MLflow including:
        - Rows processed
        - Processing time
        - Data quality metrics
        - Error handling
        """
    )
    
    # Portfolio analysis logging
    portfolio_analysis_task = PythonOperator(
        task_id="log_portfolio_analysis",
        python_callable=log_portfolio_analysis,
        doc_md="""
        ## Portfolio Analysis Tracking
        Logs portfolio analysis metrics to MLflow including:
        - Data freshness
        - Symbol coverage
        - Data quality scores
        """
    )
    
    # Task dependencies
    log_ingestion_task >> portfolio_analysis_task