# dags/knime_cli_dag.py
# Orchestration: Triggered by Airbyte data ingestion via Dataset

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.datasets import Dataset
from datetime import datetime

# Dataset produced by Airbyte sync
airbyte_dataset = Dataset("mysql://mansa_bot/binance_ohlcv")

# Dataset produced by KNIME for MLflow
knime_dataset = Dataset("mysql://mansa_bot/knime_processed")

default_args = {
    'start_date': datetime(2023, 1, 1),
    'catchup': False
}

with DAG(
    'knime_cli_workflow', 
    default_args=default_args, 
    schedule=[airbyte_dataset],  # Triggered when Airbyte produces data
    catchup=False,
    tags=['knime', 'data-processing', 'orchestration']
) as dag:

    run_knime = BashOperator(
        task_id='run_knime_workflow',
        bash_command="""
        echo "KNIME workflow placeholder - configure with actual KNIME path"
        echo "Processing data from airbyte_sync_dag..."
        # /path/to/knime -nosplash -application org.knime.product.KNIME_BATCH_APPLICATION \
        # -workflowFile="/path/to/workflow.knwf" \
        # -reset
        """,
        outlets=[knime_dataset]  # Produces dataset for MLflow
    )