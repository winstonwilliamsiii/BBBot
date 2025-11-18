# dags/airbyte_sync_dag.py
"""
Bentley Budget Bot - Airbyte Integration DAG
Triggers Airbyte data synchronization and monitors completion
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import requests
import logging
import time

# Configuration
AIRBYTE_API = "http://localhost:8001"  # Airbyte API endpoint (Docker)
CONNECTION_ID = "your-connection-id"   # Update with actual connection ID
MAX_WAIT_TIME = 3600  # Maximum wait time in seconds (1 hour)

def check_airbyte_health(**context):
    """Check if Airbyte API is accessible"""
    try:
        health_url = f"{AIRBYTE_API}/health"
        response = requests.get(health_url, timeout=10)
        response.raise_for_status()
        logging.info("✅ Airbyte API is healthy")
        return True
    except Exception as e:
        logging.error(f"❌ Airbyte health check failed: {e}")
        raise

def trigger_airbyte_sync(**context):
    """Trigger Airbyte sync job"""
    try:
        url = f"{AIRBYTE_API}/v1/connections/sync"
        payload = {"connectionId": CONNECTION_ID}
        
        logging.info(f"🔄 Triggering Airbyte sync for connection: {CONNECTION_ID}")
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        job_data = response.json()
        job_id = job_data.get("job", {}).get("id")
        
        if job_id:
            logging.info(f"✅ Sync job started successfully: {job_id}")
            # Store job_id in XCom for next task
            context['task_instance'].xcom_push(key='job_id', value=job_id)
            return job_id
        else:
            raise Exception("No job ID returned from Airbyte API")
            
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Failed to trigger Airbyte sync: {e}")
        raise
    except Exception as e:
        logging.error(f"❌ Unexpected error in sync trigger: {e}")
        raise

def wait_for_sync_completion(**context):
    """Poll Airbyte for sync completion"""
    try:
        # Get job_id from previous task
        job_id = context['task_instance'].xcom_pull(
            key='job_id',
            task_ids='trigger_airbyte_sync'
        )
        
        if not job_id:
            raise Exception("No job ID found from previous task")
        
        logging.info(f"🔍 Monitoring sync job: {job_id}")
        
        start_time = time.time()
        while time.time() - start_time < MAX_WAIT_TIME:
            try:
                status_url = f"{AIRBYTE_API}/v1/jobs/{job_id}"
                response = requests.get(status_url, timeout=10)
                response.raise_for_status()
                
                job_status = response.json()
                status = job_status.get("job", {}).get("status")
                
                logging.info(f"📊 Job status: {status}")
                
                if status == "succeeded":
                    logging.info("✅ Airbyte sync completed successfully!")
                    return "SUCCESS"
                elif status == "failed":
                    raise Exception(f"❌ Airbyte sync job failed: {job_id}")
                elif status in ["running", "pending"]:
                    logging.info(f"⏳ Job still {status}, waiting...")
                    time.sleep(30)  # Wait 30 seconds before next check
                else:
                    logging.warning(f"⚠️ Unknown status: {status}")
                    time.sleep(30)
                    
            except requests.exceptions.RequestException as e:
                logging.warning(f"⚠️ Status check failed: {e}, retrying...")
                time.sleep(30)
        
        # Timeout reached
        raise Exception(f"❌ Sync job timeout after {MAX_WAIT_TIME} seconds")
        
    except Exception as e:
        logging.error(f"❌ Error monitoring sync: {e}")
        raise

# Default DAG arguments
default_args = {
    'owner': 'bentley-bot',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 17),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
with DAG(
    'airbyte_sync_dag',
    default_args=default_args,
    description='Bentley Budget Bot - Airbyte Data Sync',
    schedule_interval=timedelta(hours=6),  # Run every 6 hours
    catchup=False,
    tags=['bentley-bot', 'airbyte', 'data-sync']
) as dag:

    # Health check task
    health_check = PythonOperator(
        task_id='check_airbyte_health',
        python_callable=check_airbyte_health,
        doc_md="""
        ## Airbyte Health Check
        Verifies that the Airbyte API is accessible before starting sync.
        """
    )

    # Trigger sync task
    sync_airbyte = PythonOperator(
        task_id='trigger_airbyte_sync',
        python_callable=trigger_airbyte_sync,
        doc_md="""
        ## Trigger Airbyte Sync
        Initiates data synchronization job in Airbyte.
        Returns job ID for monitoring.
        """
    )

    # Wait for completion task
    wait_sync = PythonOperator(
        task_id='wait_for_sync_completion',
        python_callable=wait_for_sync_completion,
        doc_md="""
        ## Monitor Sync Completion
        Polls Airbyte API to monitor sync job progress.
        Completes when sync is successful or fails after timeout.
        """
    )

    # Optional: Log completion
    log_completion = BashOperator(
        task_id='log_sync_completion',
        bash_command='echo "✅ Bentley Bot Airbyte sync completed at $(date)"'
    )

    # Task dependencies
    health_check >> sync_airbyte >> wait_sync >> log_completion