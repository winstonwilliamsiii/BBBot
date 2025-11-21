# Airbyte Data Integration DAGs
# This folder contains DAGs that manage Airbyte connections and data pipelines

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import requests
import logging

# Airbyte Configuration
AIRBYTE_API_BASE = "http://localhost:8001/api/v1"
AIRBYTE_SERVER = "http://localhost:8001"

default_args = {
    'owner': 'bentley-budget-bot',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 21),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# === Airbyte Data Sync DAG ===
dag_data_sync = DAG(
    'airbyte_data_sync',
    default_args=default_args,
    description='Sync financial data sources via Airbyte',
    schedule_interval='@hourly',
    catchup=False,
    tags=['airbyte', 'data-integration', 'etl']
)

def trigger_airbyte_connection(connection_id):
    """Trigger an Airbyte connection sync"""
    url = f"{AIRBYTE_API_BASE}/connections/sync"
    payload = {"connectionId": connection_id}
    
    response = requests.post(url, json=payload, timeout=30)
    if response.status_code == 200:
        logging.info(f"Successfully triggered sync for connection {connection_id}")
        return response.json()
    else:
        raise Exception(f"Failed to trigger sync: {response.text}")

def check_connection_status(connection_id):
    """Check the status of an Airbyte connection"""
    url = f"{AIRBYTE_API_BASE}/connections/get"
    payload = {"connectionId": connection_id}
    
    response = requests.post(url, json=payload, timeout=30)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to check connection status: {response.text}")

# Example tasks for Airbyte data sources
sync_yahoo_finance = PythonOperator(
    task_id='sync_yahoo_finance_data',
    python_callable=trigger_airbyte_connection,
    op_args=['your-yahoo-finance-connection-id'],
    dag=dag_data_sync
)

sync_banking_data = PythonOperator(
    task_id='sync_banking_data',
    python_callable=trigger_airbyte_connection,
    op_args=['your-banking-connection-id'],
    dag=dag_data_sync
)

# Task dependencies
sync_yahoo_finance >> sync_banking_data

# === Airbyte Health Check DAG ===
dag_health_check = DAG(
    'airbyte_health_check',
    default_args=default_args,
    description='Monitor Airbyte service health',
    schedule_interval='*/15 * * * *',  # Every 15 minutes
    catchup=False,
    tags=['airbyte', 'monitoring', 'health-check']
)

def check_airbyte_health():
    """Check if Airbyte server is healthy"""
    try:
        response = requests.get(f"{AIRBYTE_SERVER}/health", timeout=10)
        if response.status_code == 200:
            logging.info("Airbyte server is healthy")
            return True
        else:
            raise Exception(f"Airbyte health check failed: {response.status_code}")
    except Exception as e:
        logging.error(f"Airbyte health check error: {str(e)}")
        raise

health_check_task = PythonOperator(
    task_id='check_airbyte_health',
    python_callable=check_airbyte_health,
    dag=dag_health_check
)

# === Connection Management DAG ===
dag_connection_mgmt = DAG(
    'airbyte_connection_management',
    default_args=default_args,
    description='Manage Airbyte connections and configurations',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['airbyte', 'management', 'configuration']
)

def list_all_connections():
    """List all Airbyte connections"""
    url = f"{AIRBYTE_API_BASE}/connections/list"
    payload = {"workspaceId": "your-workspace-id"}
    
    response = requests.post(url, json=payload, timeout=30)
    if response.status_code == 200:
        connections = response.json().get('connections', [])
        logging.info(f"Found {len(connections)} connections")
        for conn in connections:
            logging.info(f"Connection: {conn.get('name')} (ID: {conn.get('connectionId')})")
        return connections
    else:
        raise Exception(f"Failed to list connections: {response.text}")

list_connections_task = PythonOperator(
    task_id='list_airbyte_connections',
    python_callable=list_all_connections,
    dag=dag_connection_mgmt
)