"""
Integration tests for Bentley Budget Bot services.

Tests verify that:
1. Docker compose files are valid
2. DAG syntax is correct
3. MLflow integration is properly configured
4. All required files exist
"""

import os
import yaml
import ast
import subprocess


def test_docker_compose_files_valid():
    """Test that all docker-compose files have valid YAML syntax."""
    compose_files = [
        'docker-compose-airflow.yml',
        'docker-compose-airbyte.yml',
        'docker-compose.yml'
    ]
    
    for filename in compose_files:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        assert os.path.exists(filepath), f"{filename} not found"
        
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
            assert data is not None, f"{filename} contains invalid YAML"
            assert 'services' in data, f"{filename} missing services section"
        
        print(f"✓ {filename} is valid")


def test_airflow_compose_has_mlflow():
    """Test that MLflow service is defined in Airflow compose file."""
    filepath = os.path.join(
        os.path.dirname(__file__),
        'docker-compose-airflow.yml'
    )
    
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
        
    assert 'mlflow' in data['services'], "MLflow service not found"
    
    mlflow_service = data['services']['mlflow']
    assert 'ports' in mlflow_service, "MLflow ports not configured"
    assert '5000:5000' in mlflow_service['ports'], "MLflow port not 5000"
    
    env = mlflow_service.get('environment', [])
    env_dict = {}
    for item in env:
        if isinstance(item, str) and '=' in item:
            key, val = item.split('=', 1)
            env_dict[key] = val
    
    assert 'MLFLOW_BACKEND_STORE_URI' in env_dict, \
        "MLflow backend store not configured"
    assert 'mlflow_db' in env_dict['MLFLOW_BACKEND_STORE_URI'], \
        "MLflow not using mlflow_db"
    
    print("✓ MLflow service properly configured in docker-compose")


def test_mlflow_volume_defined():
    """Test that MLflow artifacts volume is defined."""
    filepath = os.path.join(
        os.path.dirname(__file__),
        'docker-compose-airflow.yml'
    )
    
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)
    
    assert 'volumes' in data, "Volumes section not found"
    assert 'mlflow_artifacts' in data['volumes'], \
        "MLflow artifacts volume not defined"
    
    print("✓ MLflow artifacts volume defined")


def test_dag_syntax_valid():
    """Test that the DAG file has valid Python syntax."""
    dag_files = [
        'src/Bentleybot_dag.py',
        '.vscode/bentleybot_dag.py'
    ]
    
    for dag_file in dag_files:
        filepath = os.path.join(os.path.dirname(__file__), dag_file)
        assert os.path.exists(filepath), f"{dag_file} not found"
        
        with open(filepath, 'r') as f:
            code = f.read()
        
        try:
            ast.parse(code)
            print(f"✓ {dag_file} has valid Python syntax")
        except SyntaxError as e:
            raise AssertionError(f"{dag_file} has syntax error: {e}")


def test_dag_line_lengths():
    """Test that DAG file complies with PEP 8 line length (79 chars)."""
    dag_file = 'src/Bentleybot_dag.py'
    filepath = os.path.join(os.path.dirname(__file__), dag_file)
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    long_lines = []
    for i, line in enumerate(lines, 1):
        if len(line.rstrip()) > 79:
            long_lines.append((i, len(line.rstrip())))
    
    assert len(long_lines) == 0, \
        f"Lines exceed 79 chars: {long_lines}"
    
    print(f"✓ {dag_file} complies with PEP 8 line length")


def test_dag_has_mlflow_integration():
    """Test that DAG includes MLflow tracking code."""
    dag_file = 'src/Bentleybot_dag.py'
    filepath = os.path.join(os.path.dirname(__file__), dag_file)
    
    with open(filepath, 'r') as f:
        code = f.read()
    
    # Check for MLflow imports
    assert 'import mlflow' in code, "MLflow not imported"
    
    # Check for MLflow tracking URI
    assert 'mlflow.set_tracking_uri' in code, \
        "MLflow tracking URI not set"
    
    # Check for MLflow experiment
    assert 'mlflow.set_experiment' in code, \
        "MLflow experiment not set"
    
    # Check for MLflow run
    assert 'mlflow.start_run' in code, "MLflow run not started"
    
    # Check for metric logging
    assert 'mlflow.log_metric' in code, "MLflow metrics not logged"
    
    # Check for artifact logging
    assert 'mlflow.log_artifact' in code, "MLflow artifacts not logged"
    
    # Check for correct container name
    assert 'http://mlflow:5000' in code, \
        "MLflow URI should use container name 'mlflow'"
    
    print("✓ DAG has complete MLflow integration")


def test_dag_has_mlflow_task():
    """Test that DAG includes a task to log to MLflow."""
    dag_file = 'src/Bentleybot_dag.py'
    filepath = os.path.join(os.path.dirname(__file__), dag_file)
    
    with open(filepath, 'r') as f:
        code = f.read()
    
    # Check for log_to_mlflow function
    assert 'def log_to_mlflow' in code, \
        "log_to_mlflow function not defined"
    
    # Check for PythonOperator task
    assert 'task_id="log_mlflow"' in code or \
           "task_id='log_mlflow'" in code, \
        "log_mlflow task not defined"
    
    # Check for task dependencies
    assert 't5' in code, "Task t5 not defined"
    assert 't1 >> t2 >> t3 >> t4 >> t5' in code, \
        "Task dependencies not properly set"
    
    print("✓ DAG has MLflow task with proper dependencies")


def test_mysql_setup_has_mlflow_db():
    """Test that MySQL setup script creates MLflow database."""
    filepath = os.path.join(
        os.path.dirname(__file__),
        'mysql_setup.sql'
    )
    
    with open(filepath, 'r') as f:
        sql = f.read()
    
    assert 'CREATE DATABASE IF NOT EXISTS mlflow_db' in sql, \
        "MLflow database creation not found"
    
    assert 'GRANT ALL PRIVILEGES ON mlflow_db.*' in sql, \
        "MLflow database permissions not granted"
    
    print("✓ MySQL setup includes MLflow database")


def test_documentation_exists():
    """Test that all required documentation files exist."""
    docs = [
        'MLFLOW_INTEGRATION.md',
        'SERVICES_QUICK_START.md',
        'DOCKER_SERVICES_GUIDE.md',
        'README.md'
    ]
    
    for doc in docs:
        filepath = os.path.join(os.path.dirname(__file__), doc)
        assert os.path.exists(filepath), f"{doc} not found"
        
        # Check file is not empty
        size = os.path.getsize(filepath)
        assert size > 100, f"{doc} is too small ({size} bytes)"
        
        print(f"✓ {doc} exists and is not empty")


def test_troubleshooting_script_exists():
    """Test that troubleshooting PowerShell script exists."""
    filepath = os.path.join(
        os.path.dirname(__file__),
        'troubleshoot_services.ps1'
    )
    
    assert os.path.exists(filepath), \
        "troubleshoot_services.ps1 not found"
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check for key sections
    assert 'Checking Docker status' in content or \
           'Check Docker status' in content
    assert 'port availability' in content
    assert 'Docker containers' in content
    assert 'service health' in content
    
    print("✓ troubleshoot_services.ps1 exists with all sections")


def test_manage_services_includes_mlflow():
    """Test that manage_services.ps1 mentions MLflow."""
    filepath = os.path.join(
        os.path.dirname(__file__),
        'manage_services.ps1'
    )
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    assert 'MLflow' in content or 'mlflow' in content, \
        "manage_services.ps1 doesn't mention MLflow"
    
    assert '5000' in content, \
        "manage_services.ps1 doesn't mention port 5000"
    
    print("✓ manage_services.ps1 includes MLflow information")


def test_readme_updated():
    """Test that README has been updated with new information."""
    filepath = os.path.join(os.path.dirname(__file__), 'README.md')
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check for MLflow mention
    assert 'MLflow' in content or 'mlflow' in content, \
        "README doesn't mention MLflow"
    
    # Check for documentation links
    assert 'SERVICES_QUICK_START.md' in content, \
        "README doesn't link to SERVICES_QUICK_START.md"
    
    assert 'MLFLOW_INTEGRATION.md' in content, \
        "README doesn't link to MLFLOW_INTEGRATION.md"
    
    # Check for port 5000
    assert '5000' in content, \
        "README doesn't mention MLflow port 5000"
    
    print("✓ README.md has been updated with MLflow information")


if __name__ == '__main__':
    print("Running Bentley Budget Bot Integration Tests")
    print("=" * 50)
    
    tests = [
        test_docker_compose_files_valid,
        test_airflow_compose_has_mlflow,
        test_mlflow_volume_defined,
        test_dag_syntax_valid,
        test_dag_line_lengths,
        test_dag_has_mlflow_integration,
        test_dag_has_mlflow_task,
        test_mysql_setup_has_mlflow_db,
        test_documentation_exists,
        test_troubleshooting_script_exists,
        test_manage_services_includes_mlflow,
        test_readme_updated,
    ]
    
    failed = []
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed.append(test.__name__)
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            failed.append(test.__name__)
    
    print("=" * 50)
    if failed:
        print(f"\n❌ {len(failed)} test(s) failed:")
        for name in failed:
            print(f"  - {name}")
        exit(1)
    else:
        print(f"\n✅ All {len(tests)} tests passed!")
        exit(0)
