# Docker operator for Bentley Budget Bot
import subprocess

try:
    from airflow.providers.docker.operators.docker import DockerOperator
    AIRFLOW_AVAILABLE = True
except ImportError:
    # Fallback when Airflow is not installed
    AIRFLOW_AVAILABLE = False
    DockerOperator = None


def create_docker_operator():
    """Create Docker operator if Airflow is available."""
    if not AIRFLOW_AVAILABLE:
        return None
        
    return DockerOperator(
        task_id='run_indicators',
        image='bentleybot:latest',
        api_version='auto',
        auto_remove=True,
        command='python /app/compute_indicators.py',
        docker_url='unix://var/run/docker.sock',
        network_mode='bridge',
        volumes=['/host/data:/app/data']
    )


def run_docker_command():
    """Run Docker command directly when Airflow is not available."""
    cmd = [
        'docker', 'run', '--rm',
        '-v', '/host/data:/app/data',
        'bentleybot:latest',
        'python', '/app/compute_indicators.py'
    ]
    return subprocess.run(cmd, capture_output=True, text=True)


# Create the operator if Airflow is available
run_indicators = create_docker_operator()


# DAG Definition (only if Airflow is available)
if AIRFLOW_AVAILABLE:
    from airflow import DAG
    from datetime import datetime, timedelta
    
    default_args = {
        'owner': 'winston',
        'start_date': datetime(2025, 11, 10),
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    }

    with DAG(
        dag_id='rsi_macd_docker_pipeline',
        default_args=default_args,
        schedule_interval='@daily',
        catchup=False,
        tags=['docker', 'indicators'],
    ) as dag:

        run_indicators_task = DockerOperator(
            task_id='compute_indicators_container',
            image='bentleybot-indicators:latest',
            api_version='auto',
            auto_remove=True,
            command='python /app/compute_indicators.py',
            docker_url='unix://var/run/docker.sock',
            network_mode='bridge',
            volumes=['/host/data:/app/data']
        )