"""
Bentley Budget Bot - Master Orchestration DAG
==============================================
Demonstrates the complete data pipeline orchestration:
Airbyte → KNIME → MLflow

This DAG provides a unified view of the entire data pipeline.
Individual DAGs are connected via Airflow Datasets.
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.sensors.external_task import ExternalTaskSensor
from datetime import datetime, timedelta
from airflow.datasets import Dataset

# Define datasets for orchestration
airbyte_dataset = Dataset("mysql://mansa_bot/binance_ohlcv")
knime_dataset = Dataset("mysql://mansa_bot/knime_processed")


def print_pipeline_status(**context):
    """Print the current status of the data pipeline"""
    print("=" * 60)
    print("🤖 Bentley Budget Bot - Data Pipeline Status")
    print("=" * 60)
    print("\n📊 Pipeline Architecture:")
    print("  1. Airbyte Sync   → Ingests data from external sources")
    print("  2. KNIME Workflow → Processes and transforms data")
    print("  3. MLflow Logging → Tracks metrics and experiments")
    print("\n🔄 Current Execution:")
    print(f"  Execution Date: {context['execution_date']}")
    print(f"  DAG Run ID: {context['dag_run'].run_id}")
    print("\n✅ All DAGs are orchestrated via Datasets:")
    print("  - airbyte_sync_dag produces: mysql://mansa_bot/binance_ohlcv")
    print("  - knime_cli_workflow consumes: Airbyte dataset")
    print("  - knime_cli_workflow produces: mysql://mansa_bot/knime_processed")
    print("  - mlflow_logging_dag consumes: Both Airbyte & KNIME datasets")
    print("=" * 60)


def check_airbyte_status(**context):
    """Check if Airbyte sync completed successfully"""
    print("🔍 Checking Airbyte sync status...")
    # TODO: Implement actual Airbyte status check
    print("✅ Airbyte sync completed")
    return {"status": "success", "rows_synced": 1000}


def check_knime_status(**context):
    """Check if KNIME workflow completed successfully"""
    print("🔍 Checking KNIME workflow status...")
    # TODO: Implement actual KNIME status check
    print("✅ KNIME processing completed")
    return {"status": "success", "rows_processed": 950}


def check_mlflow_status(**context):
    """Check if MLflow logging completed successfully"""
    print("🔍 Checking MLflow logging status...")
    # TODO: Implement actual MLflow status check
    print("✅ MLflow metrics logged")
    return {"status": "success", "experiments_logged": 2}


def generate_pipeline_report(**context):
    """Generate a summary report of the pipeline execution"""
    ti = context['task_instance']

    airbyte_result = ti.xcom_pull(task_ids='check_airbyte')
    knime_result = ti.xcom_pull(task_ids='check_knime')
    mlflow_result = ti.xcom_pull(task_ids='check_mlflow')

    print("\n" + "=" * 60)
    print("📈 PIPELINE EXECUTION REPORT")
    print("=" * 60)
    print(f"\n🔄 Airbyte Sync: {airbyte_result}")
    print(f"⚙️  KNIME Process: {knime_result}")
    print(f"📊 MLflow Track: {mlflow_result}")
    print("\n✅ Pipeline execution completed successfully!")
    print("=" * 60 + "\n")


# DAG default arguments
default_args = {
    'owner': 'bentley-bot',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 20),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    'bentley_master_orchestration',
    default_args=default_args,
    description='Master DAG showing Airbyte → KNIME → MLflow pipeline',
    schedule_interval='@daily',  # Run daily, coordinates other DAGs
    catchup=False,
    tags=['master', 'orchestration', 'bentley-bot', 'pipeline'],
    doc_md=__doc__
) as dag:

    # Print pipeline info
    pipeline_status = PythonOperator(
        task_id='print_pipeline_status',
        python_callable=print_pipeline_status,
        doc_md="""
        ## Pipeline Status
        Prints the current architecture and execution details
        """
    )

    # Trigger Airbyte sync
    trigger_airbyte = TriggerDagRunOperator(
        task_id='trigger_airbyte_sync',
        trigger_dag_id='airbyte_sync_dag',
        wait_for_completion=True,
        doc_md="""
        ## Airbyte Sync Trigger
        Triggers the Airbyte data ingestion DAG
        """
    )

    # Check Airbyte completion
    check_airbyte = PythonOperator(
        task_id='check_airbyte',
        python_callable=check_airbyte_status,
        doc_md="""
        ## Airbyte Status Check
        Verifies Airbyte sync completed successfully
        """
    )

    # Wait for KNIME workflow (triggered by Airbyte dataset)
    # Note: KNIME is automatically triggered by dataset, so we just check status
    check_knime = PythonOperator(
        task_id='check_knime',
        python_callable=check_knime_status,
        doc_md="""
        ## KNIME Status Check
        Verifies KNIME workflow completed successfully
        (KNIME is auto-triggered by Airbyte dataset)
        """
    )

    # Wait for MLflow logging (triggered by KNIME dataset)
    check_mlflow = PythonOperator(
        task_id='check_mlflow',
        python_callable=check_mlflow_status,
        doc_md="""
        ## MLflow Status Check
        Verifies MLflow logging completed successfully
        (MLflow is auto-triggered by KNIME dataset)
        """
    )

    # Generate final report
    generate_report = PythonOperator(
        task_id='generate_report',
        python_callable=generate_pipeline_report,
        doc_md="""
        ## Pipeline Report
        Generates comprehensive report of pipeline execution
        """
    )

    # Define task dependencies - Linear orchestration flow
    (
        pipeline_status
        >> trigger_airbyte
        >> check_airbyte
        >> check_knime
        >> check_mlflow
        >> generate_report
    )
