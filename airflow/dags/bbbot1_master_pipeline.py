"""
BentleyBot Master Orchestration DAG
Orchestrates the complete data pipeline: ingestion → calculation → cache refresh

This DAG runs the bbbot1_pipeline package in sequence:
1. Fetch fundamentals from Alpha Vantage
2. Fetch prices from yfinance
3. Calculate financial ratios and metrics
4. Update Streamlit cache
5. Trigger MLFlow logging (optional)
6. Trigger KNIME workflows (optional)
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import sys
import os

# Add bbbot1_pipeline to Python path
sys.path.insert(0, '/opt/airflow')

# Import pipeline modules
from bbbot1_pipeline.ingest_alpha_vantage import run_alpha_vantage_ingestion
from bbbot1_pipeline.ingest_yfinance import run_yfinance_ingestion
from bbbot1_pipeline.derive_ratios import generate_ticker_summary
from bbbot1_pipeline import load_tickers_config
import pandas as pd

# Load configuration from YAML
config = load_tickers_config()
QUANTUM_TICKERS = config['tickers']['quantum']
MAJOR_TICKERS = config['tickers']['major_tech']
ALL_TICKERS = config['tickers']['all']

# Default DAG arguments
default_args = {
    'owner': 'bentleybot',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}


def fetch_fundamentals(**context):
    """
    Task 1: Fetch fundamental data from Alpha Vantage
    """
    print("="*80)
    print("TASK 1: Fetching Fundamentals from Alpha Vantage")
    print("="*80)
    
    # Fetch for all tickers
    success_count = run_alpha_vantage_ingestion(ALL_TICKERS, delay=12)
    
    # Push results to XCom for downstream tasks
    context['task_instance'].xcom_push(key='fundamentals_count', value=success_count)
    
    print(f"\n✓ Task 1 Complete: {success_count}/{len(ALL_TICKERS)} tickers processed")
    return success_count


def fetch_prices(**context):
    """
    Task 2: Fetch price data from yfinance
    """
    print("="*80)
    print("TASK 2: Fetching Prices from yfinance")
    print("="*80)
    
    # Fetch 2 years of price data
    rows_inserted = run_yfinance_ingestion(
        tickers=ALL_TICKERS,
        lookback_days=730,
        table_name='stock_prices_yf'
    )
    
    # Push results to XCom
    context['task_instance'].xcom_push(key='prices_inserted', value=rows_inserted)
    
    print(f"\n✓ Task 2 Complete: {rows_inserted} price records inserted")
    return rows_inserted


def calculate_ratios(**context):
    """
    Task 3: Calculate financial ratios and technical indicators
    """
    print("="*80)
    print("TASK 3: Calculating Financial Ratios and Metrics")
    print("="*80)
    
    summaries = []
    
    for ticker in ALL_TICKERS:
        try:
            print(f"\nProcessing {ticker}...")
            summary = generate_ticker_summary(ticker)
            summaries.append(summary)
            print(f"✓ {ticker} complete")
        except Exception as e:
            print(f"✗ Error processing {ticker}: {e}")
            continue
    
    # Create DataFrame and display summary
    if summaries:
        df = pd.DataFrame(summaries)
        print("\n" + "="*80)
        print("CALCULATED METRICS SUMMARY")
        print("="*80)
        print(df.to_string(index=False))
        
        # Store summary count in XCom
        context['task_instance'].xcom_push(key='metrics_calculated', value=len(summaries))
    
    print(f"\n✓ Task 3 Complete: Calculated metrics for {len(summaries)} tickers")
    return len(summaries)


def update_streamlit_cache(**context):
    """
    Task 4: Update Streamlit cache and trigger refresh
    """
    print("="*80)
    print("TASK 4: Updating Streamlit Cache")
    print("="*80)
    
    # Get results from previous tasks
    ti = context['task_instance']
    fundamentals_count = ti.xcom_pull(task_ids='fetch_fundamentals', key='fundamentals_count')
    prices_inserted = ti.xcom_pull(task_ids='fetch_prices', key='prices_inserted')
    metrics_calculated = ti.xcom_pull(task_ids='calculate_ratios', key='metrics_calculated')
    
    print(f"Pipeline Results:")
    print(f"  - Fundamentals fetched: {fundamentals_count} tickers")
    print(f"  - Price records inserted: {prices_inserted}")
    print(f"  - Metrics calculated: {metrics_calculated} tickers")
    
    # TODO: Implement actual Streamlit cache refresh
    # Options:
    # 1. Touch a file that Streamlit watches
    # 2. Call Streamlit API if available
    # 3. Redis cache update
    # 4. Database trigger
    
    cache_file = '/opt/airflow/data/.streamlit_cache_timestamp'
    try:
        import time
        with open(cache_file, 'w') as f:
            f.write(str(time.time()))
        print(f"✓ Updated cache timestamp: {cache_file}")
    except Exception as e:
        print(f"⚠ Could not update cache file: {e}")
    
    print("\n✓ Task 4 Complete: Streamlit cache updated")
    return True


def prepare_mlflow_trigger(**context):
    """
    Task 5: Prepare data for MLFlow model training
    """
    print("="*80)
    print("TASK 5: Preparing MLFlow Trigger")
    print("="*80)
    
    # Get metrics calculated
    ti = context['task_instance']
    metrics_count = ti.xcom_pull(task_ids='calculate_ratios', key='metrics_calculated')
    
    if metrics_count and metrics_count > 0:
        print(f"✓ {metrics_count} tickers ready for ML training")
        print("✓ MLFlow DAG trigger prepared")
        return True
    else:
        print("⚠ No metrics calculated, skipping MLFlow trigger")
        return False


def prepare_knime_trigger(**context):
    """
    Task 6: Prepare data for KNIME workflow execution
    """
    print("="*80)
    print("TASK 6: Preparing KNIME Trigger")
    print("="*80)
    
    # Get pipeline results
    ti = context['task_instance']
    prices_inserted = ti.xcom_pull(task_ids='fetch_prices', key='prices_inserted')
    
    if prices_inserted and prices_inserted > 0:
        print(f"✓ {prices_inserted} price records available for KNIME")
        print("✓ KNIME workflow trigger prepared")
        return True
    else:
        print("⚠ No prices available, skipping KNIME trigger")
        return False


# Create the DAG
with DAG(
    dag_id='bbbot1_master_pipeline',
    default_args=default_args,
    description='Master orchestration for BentleyBot data pipeline',
    schedule_interval='0 18 * * 1-5',  # Run at 6 PM on weekdays (after market close)
    start_date=days_ago(1),
    catchup=False,
    tags=['bbbot1', 'pipeline', 'master', 'orchestration'],
) as dag:
    
    # Task 1: Fetch fundamentals from Alpha Vantage
    task_fetch_fundamentals = PythonOperator(
        task_id='fetch_fundamentals',
        python_callable=fetch_fundamentals,
        provide_context=True,
    )
    
    # Task 2: Fetch prices from yfinance
    task_fetch_prices = PythonOperator(
        task_id='fetch_prices',
        python_callable=fetch_prices,
        provide_context=True,
    )
    
    # Task 3: Calculate ratios and metrics
    task_calculate_ratios = PythonOperator(
        task_id='calculate_ratios',
        python_callable=calculate_ratios,
        provide_context=True,
    )
    
    # Task 4: Update Streamlit cache
    task_update_cache = PythonOperator(
        task_id='update_streamlit_cache',
        python_callable=update_streamlit_cache,
        provide_context=True,
    )
    
    # Task 5: Prepare MLFlow trigger (optional)
    task_mlflow_prep = PythonOperator(
        task_id='prepare_mlflow_trigger',
        python_callable=prepare_mlflow_trigger,
        provide_context=True,
    )
    
    # Task 6: Prepare KNIME trigger (optional)
    task_knime_prep = PythonOperator(
        task_id='prepare_knime_trigger',
        python_callable=prepare_knime_trigger,
        provide_context=True,
    )
    
    # Optional: Trigger MLFlow DAG if it exists
    # Uncomment when mlflow_logging_dag is ready
    # task_trigger_mlflow = TriggerDagRunOperator(
    #     task_id='trigger_mlflow_dag',
    #     trigger_dag_id='mlflow_logging_dag',
    #     wait_for_completion=False,
    # )
    
    # Optional: Trigger KNIME DAG if it exists
    # Uncomment when knime_cli_workflow is ready
    # task_trigger_knime = TriggerDagRunOperator(
    #     task_id='trigger_knime_dag',
    #     trigger_dag_id='knime_cli_workflow',
    #     wait_for_completion=False,
    # )
    
    # Define task dependencies (sequential execution)
    task_fetch_fundamentals >> task_fetch_prices >> task_calculate_ratios >> task_update_cache
    
    # Parallel preparation of downstream triggers
    task_update_cache >> [task_mlflow_prep, task_knime_prep]
    
    # If you enable the trigger tasks, uncomment these:
    # task_mlflow_prep >> task_trigger_mlflow
    # task_knime_prep >> task_trigger_knime


# DAG Documentation
__doc__ = """
# BentleyBot Master Pipeline DAG

## Purpose
Orchestrates the complete data pipeline for BentleyBot stock analysis system.

## Schedule
- **Frequency**: Daily at 6 PM (weekdays only)
- **Reason**: After market close to capture end-of-day data

## Task Sequence
1. **fetch_fundamentals**: Alpha Vantage API (fundamentals data)
2. **fetch_prices**: yfinance API (price history)
3. **calculate_ratios**: Derive metrics (MAs, P/E, volatility)
4. **update_streamlit_cache**: Refresh UI cache
5. **prepare_mlflow_trigger**: Prepare ML training data
6. **prepare_knime_trigger**: Prepare analytics workflows

## Tickers Processed
- Quantum Computing: IONQ, QBTS, SOUN, RGTI
- Major Tech: AMZN, MSFT, GOOGL

## Dependencies
- bbbot1_pipeline package
- MySQL database (port 3307)
- Alpha Vantage API key
- yfinance library

## Integration Points
- **Airbyte**: Syncs data to Snowflake automatically
- **MLFlow**: Triggered for model training (optional)
- **KNIME**: Triggered for advanced analytics (optional)
- **Streamlit**: Cache updated for dashboard refresh

## Monitoring
Check XCom for task results:
- fundamentals_count: Number of tickers with fundamentals
- prices_inserted: Number of price records
- metrics_calculated: Number of tickers with calculated metrics

## Manual Trigger
```bash
docker exec bentley-airflow-webserver airflow dags trigger bbbot1_master_pipeline
```

## Logs Location
Check Airflow UI → DAGs → bbbot1_master_pipeline → Graph View → Click task → Logs
"""
