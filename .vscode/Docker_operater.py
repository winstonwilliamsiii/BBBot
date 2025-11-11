from airflow.providers.docker.operators.docker import DockerOperator

run_indicators = DockerOperator(
    task_id='run_indicators',
    image='bentleybot:latest',
    api_version='auto',
    auto_remove=True,
    command='python /app/compute_indicators.py',
    docker_url='unix://var/run/docker.sock',
    network_mode='bridge',
    volumes=['/host/data:/app/data']
)