"""
Airflow DAG for Stocktwits Sentiment Data Pipeline
Orchestrates scraping sentiment data and storing in MySQL
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.datasets import Dataset
from datetime import datetime, timedelta
import os
import sys

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Dataset for downstream orchestration
stocktwits_dataset = Dataset("mysql://mansa_bot/stocktwits_sentiment")

# Default arguments
default_args = {
    'owner': 'bentley-bot',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}


def run_stocktwits_scraper(**context):
    """
    Run the Stocktwits sentiment scraper using the Airbyte source
    """
    import subprocess
    import json
    import mysql.connector
    from datetime import datetime
    
    # Get MySQL connection details
    mysql_config = {
        "host": os.getenv("MYSQL_HOST", "mysql"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "root"),
        "database": os.getenv("MYSQL_DATABASE", "mansa_bot")
    }
    
    # Path to Airbyte source
    source_dir = "/opt/airflow/airbyte-source-stocktwits"
    config_file = f"{source_dir}/config.json"
    catalog_file = f"{source_dir}/catalog.json"
    
    # Run the Airbyte source connector
    cmd = [
        "python", f"{source_dir}/source.py",
        "read",
        "--config", config_file,
        "--catalog", catalog_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Stocktwits scraper failed: {result.stderr}")
    
    # Parse Airbyte records and store in MySQL
    conn = mysql.connector.connect(**mysql_config)
    cursor = conn.cursor()
    
    records_inserted = 0
    
    for line in result.stdout.strip().split('\n'):
        try:
            message = json.loads(line)
            
            if message.get("type") == "RECORD":
                data = message["record"]["data"]
                
                cursor.execute("""
                    INSERT INTO stocktwits_sentiment 
                    (ticker, sentiment_score, bullish_count, bearish_count, 
                     total_messages, scraped_at, url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    data.get("ticker"),
                    data.get("sentiment_score"),
                    data.get("bullish_count"),
                    data.get("bearish_count"),
                    data.get("total_messages"),
                    data.get("scraped_at"),
                    data.get("url")
                ))
                records_inserted += 1
        
        except json.JSONDecodeError:
            continue
    
    conn.commit()
    cursor.close()
    conn.close()
    
    context['ti'].xcom_push(key='records_inserted', value=records_inserted)
    return {"status": "success", "records_inserted": records_inserted}


def log_results(**context):
    """Log the results of the scraping"""
    import logging
    
    ti = context['ti']
    records = ti.xcom_pull(task_ids='scrape_stocktwits', key='records_inserted')
    
    logging.info(f"✅ Stocktwits sentiment scraping complete!")
    logging.info(f"📊 Records inserted: {records}")
    
    return {"records": records}


with DAG(
    'stocktwits_sentiment_pipeline',
    default_args=default_args,
    description='Scrape Stocktwits sentiment data and store in MySQL',
    schedule_interval='@hourly',  # Run every hour
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['data-ingestion', 'sentiment', 'stocktwits', 'orchestration']
) as dag:
    
    # Task 1: Run sentiment scraper
    scrape_task = PythonOperator(
        task_id='scrape_stocktwits',
        python_callable=run_stocktwits_scraper,
        provide_context=True,
        outlets=[stocktwits_dataset]
    )
    
    # Task 2: Log results
    log_task = PythonOperator(
        task_id='log_results',
        python_callable=log_results,
        provide_context=True
    )
    
    # Set task dependencies
    scrape_task >> log_task
