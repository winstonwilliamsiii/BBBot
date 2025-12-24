"""
dbt Transformation DAG
Runs dbt models after Airbyte data ingestion
Prepares data for MLFlow model training
"""

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from datetime import datetime, timedelta
import os

# dbt project path
DBT_PROJECT_PATH = os.path.join(
    os.path.dirname(__file__), 
    '../../dbt_project'
)

def check_raw_data_availability(**kwargs):
    """
    Check if raw data tables exist and have recent data
    """
    mysql_hook = MySqlHook(mysql_conn_id='mysql_bbbot1')
    conn = mysql_hook.get_conn()
    cursor = conn.cursor()
    
    tables_to_check = [
        'prices_daily',
        'fundamentals_raw',
        'sentiment_raw'
    ]
    
    results = {}
    for table in tables_to_check:
        try:
            cursor.execute(f"""
                SELECT COUNT(*) as row_count,
                       MAX(created_at) as latest_record
                FROM {table}
            """)
            row = cursor.fetchone()
            results[table] = {
                'row_count': row[0],
                'latest_record': row[1]
            }
            print(f"✓ {table}: {row[0]} rows, latest: {row[1]}")
        except Exception as e:
            print(f"⚠ {table}: {str(e)}")
            results[table] = {'error': str(e)}
    
    cursor.close()
    conn.close()
    
    # Push results to XCom
    return results

def validate_dbt_models(**kwargs):
    """
    Validate dbt model outputs
    """
    mysql_hook = MySqlHook(mysql_conn_id='mysql_bbbot1')
    conn = mysql_hook.get_conn()
    cursor = conn.cursor()
    
    models_to_check = [
        'staging.stg_prices',
        'staging.stg_fundamentals',
        'staging.stg_sentiment',
        'marts.fundamentals_derived',
        'marts.sentiment_aggregates',
        'marts.features_roi'
    ]
    
    results = {}
    for model in models_to_check:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {model}")
            row_count = cursor.fetchone()[0]
            results[model] = {'row_count': row_count}
            print(f"✓ {model}: {row_count} rows")
        except Exception as e:
            print(f"⚠ {model}: {str(e)}")
            results[model] = {'error': str(e)}
    
    cursor.close()
    conn.close()
    
    return results

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='dbt_transformation_pipeline',
    default_args=default_args,
    description='Run dbt models to transform raw data into analytics-ready datasets',
    schedule_interval='0 8 * * *',  # Daily at 8 AM (after Airbyte syncs)
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['dbt', 'transformation', 'mlflow', 'data-pipeline'],
) as dag:

    # Task 1: Check raw data availability
    check_raw_data = PythonOperator(
        task_id='check_raw_data_availability',
        python_callable=check_raw_data_availability,
        provide_context=True,
    )

    # Task 2: Run dbt debug (connection test)
    dbt_debug = BashOperator(
        task_id='dbt_debug',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt debug --profiles-dir {DBT_PROJECT_PATH}',
    )

    # Task 3: Run dbt deps (install packages)
    dbt_deps = BashOperator(
        task_id='dbt_deps',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt deps --profiles-dir {DBT_PROJECT_PATH}',
    )

    # Task 4: Run dbt staging models
    dbt_run_staging = BashOperator(
        task_id='dbt_run_staging',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt run --select staging --profiles-dir {DBT_PROJECT_PATH}',
    )

    # Task 5: Test staging models
    dbt_test_staging = BashOperator(
        task_id='dbt_test_staging',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt test --select staging --profiles-dir {DBT_PROJECT_PATH}',
    )

    # Task 6: Run dbt marts models
    dbt_run_marts = BashOperator(
        task_id='dbt_run_marts',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt run --select marts --profiles-dir {DBT_PROJECT_PATH}',
    )

    # Task 7: Test marts models
    dbt_test_marts = BashOperator(
        task_id='dbt_test_marts',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt test --select marts --profiles-dir {DBT_PROJECT_PATH}',
    )

    # Task 8: Validate model outputs
    validate_models = PythonOperator(
        task_id='validate_dbt_models',
        python_callable=validate_dbt_models,
        provide_context=True,
    )

    # Task 9: Generate dbt documentation
    dbt_docs_generate = BashOperator(
        task_id='dbt_docs_generate',
        bash_command=f'cd {DBT_PROJECT_PATH} && dbt docs generate --profiles-dir {DBT_PROJECT_PATH}',
    )

    # Task dependencies
    check_raw_data >> dbt_debug >> dbt_deps
    dbt_deps >> dbt_run_staging >> dbt_test_staging
    dbt_test_staging >> dbt_run_marts >> dbt_test_marts
    dbt_test_marts >> validate_models >> dbt_docs_generate

# DAG execution flow:
# 1. Check raw data availability (ensure Airbyte loaded data)
# 2. Test dbt connection
# 3. Install dbt dependencies
# 4. Run staging models (data cleaning)
# 5. Test staging models (data quality)
# 6. Run marts models (feature engineering)
# 7. Test marts models (data quality)
# 8. Validate final outputs
# 9. Generate documentation
