# dags/knime_cli_dag.py

from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'start_date': datetime(2023, 1, 1),
    'catchup': False
}

with DAG('knime_cli_workflow', default_args=default_args, schedule_interval='@daily') as dag:

    run_knime = BashOperator(
        task_id='run_knime_workflow',
        bash_command="""
        /path/to/knime -nosplash -application org.knime.product.KNIME_BATCH_APPLICATION \
        -workflowFile="/path/to/workflow.knwf" \
        -reset
        """
    )