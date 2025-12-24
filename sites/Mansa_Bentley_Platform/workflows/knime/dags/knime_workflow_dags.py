# KNIME Workflow Integration DAGs
# This folder contains DAGs that integrate with KNIME workflows and analytics

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import requests
import subprocess
import logging
import json
import os

# KNIME Configuration
KNIME_EXECUTOR_PATH = "/opt/knime/knime"  # Adjust path as needed
KNIME_WORKFLOWS_PATH = "/app/knime_workflows"
KNIME_SERVER_URL = "http://localhost:8080/knime"  # If using KNIME Server

default_args = {
    'owner': 'bentley-budget-bot',
    'depends_on_past': False,
    'start_date': datetime(2025, 11, 21),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# === Financial Analytics Workflow DAG ===
dag_analytics = DAG(
    'knime_financial_analytics',
    default_args=default_args,
    description='Execute KNIME workflows for financial data analytics',
    schedule_interval='@daily',
    catchup=False,
    tags=['knime', 'analytics', 'financial-modeling']
)

def execute_knime_workflow(workflow_name, workflow_path, parameters=None):
    """Execute a KNIME workflow"""
    try:
        cmd = [
            KNIME_EXECUTOR_PATH,
            "-nosplash",
            "-application",
            "org.knime.product.KNIME_BATCH_APPLICATION",
            "-workflowDir=" + workflow_path,
            "-reset"
        ]
        
        # Add workflow variables if provided
        if parameters:
            for key, value in parameters.items():
                cmd.extend(["-workflow.variable", f"{key},{value},String"])
        
        # Execute the workflow
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 min timeout
        
        if result.returncode == 0:
            logging.info(f"KNIME workflow '{workflow_name}' executed successfully")
            logging.info(f"Output: {result.stdout}")
            return True
        else:
            logging.error(f"KNIME workflow '{workflow_name}' failed")
            logging.error(f"Error: {result.stderr}")
            raise Exception(f"Workflow execution failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logging.error(f"KNIME workflow '{workflow_name}' timed out")
        raise Exception("Workflow execution timed out")
    except Exception as e:
        logging.error(f"Error executing KNIME workflow: {str(e)}")
        raise

def validate_knime_output(output_path):
    """Validate the output from KNIME workflow"""
    if not os.path.exists(output_path):
        raise Exception(f"Expected output file not found: {output_path}")
    
    # Check if the file is not empty
    if os.path.getsize(output_path) == 0:
        raise Exception(f"Output file is empty: {output_path}")
    
    logging.info(f"KNIME workflow output validated: {output_path}")
    return True

# Portfolio Risk Analysis Workflow
portfolio_risk_analysis = PythonOperator(
    task_id='portfolio_risk_analysis',
    python_callable=execute_knime_workflow,
    op_kwargs={
        'workflow_name': 'Portfolio Risk Analysis',
        'workflow_path': f"{KNIME_WORKFLOWS_PATH}/portfolio_risk_analysis",
        'parameters': {
            'data_date': '{{ ds }}',
            'risk_threshold': '0.05',
            'confidence_level': '0.95'
        }
    },
    dag=dag_analytics
)

# Market Sentiment Analysis Workflow
market_sentiment_analysis = PythonOperator(
    task_id='market_sentiment_analysis',
    python_callable=execute_knime_workflow,
    op_kwargs={
        'workflow_name': 'Market Sentiment Analysis',
        'workflow_path': f"{KNIME_WORKFLOWS_PATH}/market_sentiment",
        'parameters': {
            'analysis_date': '{{ ds }}',
            'sentiment_sources': 'twitter,reddit,news'
        }
    },
    dag=dag_analytics
)

# Technical Indicators Calculation
technical_indicators = PythonOperator(
    task_id='technical_indicators_calculation',
    python_callable=execute_knime_workflow,
    op_kwargs={
        'workflow_name': 'Technical Indicators',
        'workflow_path': f"{KNIME_WORKFLOWS_PATH}/technical_indicators",
        'parameters': {
            'calculation_date': '{{ ds }}',
            'lookback_period': '30',
            'indicators': 'RSI,MACD,BB,SMA,EMA'
        }
    },
    dag=dag_analytics
)

# Validate outputs
validate_risk_output = PythonOperator(
    task_id='validate_risk_analysis_output',
    python_callable=validate_knime_output,
    op_args=['/tmp/knime_output/portfolio_risk_results.csv'],
    dag=dag_analytics
)

validate_sentiment_output = PythonOperator(
    task_id='validate_sentiment_analysis_output',
    python_callable=validate_knime_output,
    op_args=['/tmp/knime_output/sentiment_analysis_results.csv'],
    dag=dag_analytics
)

validate_indicators_output = PythonOperator(
    task_id='validate_indicators_output',
    python_callable=validate_knime_output,
    op_args=['/tmp/knime_output/technical_indicators.csv'],
    dag=dag_analytics
)

# Task dependencies
portfolio_risk_analysis >> validate_risk_output
market_sentiment_analysis >> validate_sentiment_output
technical_indicators >> validate_indicators_output

# === KNIME Server Integration DAG ===
dag_knime_server = DAG(
    'knime_server_integration',
    default_args=default_args,
    description='Integrate with KNIME Server for enterprise workflows',
    schedule_interval='@hourly',
    catchup=False,
    tags=['knime', 'server', 'enterprise']
)

def trigger_knime_server_workflow(workflow_id, parameters=None):
    """Trigger a workflow on KNIME Server"""
    url = f"{KNIME_SERVER_URL}/rest/v4/repository/{workflow_id}:execute"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    payload = {
        'async': False,
        'timeout': 1800,  # 30 minutes
        'reset': True
    }
    
    if parameters:
        payload['workflow-variables'] = parameters
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=1800)
        
        if response.status_code == 200:
            result = response.json()
            logging.info(f"KNIME Server workflow executed successfully")
            logging.info(f"Execution ID: {result.get('executionId')}")
            return result
        else:
            raise Exception(f"KNIME Server execution failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Error connecting to KNIME Server: {str(e)}")
        raise

def check_knime_server_status():
    """Check KNIME Server health status"""
    try:
        response = requests.get(f"{KNIME_SERVER_URL}/rest/v4/health", timeout=30)
        if response.status_code == 200:
            health_data = response.json()
            logging.info(f"KNIME Server health check passed: {health_data}")
            return True
        else:
            raise Exception(f"KNIME Server health check failed: {response.status_code}")
    except Exception as e:
        logging.error(f"KNIME Server health check error: {str(e)}")
        raise

# KNIME Server tasks
server_health_check = PythonOperator(
    task_id='check_knime_server_health',
    python_callable=check_knime_server_status,
    dag=dag_knime_server
)

execute_server_workflow = PythonOperator(
    task_id='execute_real_time_analysis',
    python_callable=trigger_knime_server_workflow,
    op_kwargs={
        'workflow_id': 'bentley-bot/real-time-analysis',
        'parameters': {
            'timestamp': '{{ ts }}',
            'market_session': 'regular',
            'analysis_type': 'intraday'
        }
    },
    dag=dag_knime_server
)

# Dependencies
server_health_check >> execute_server_workflow

# === Workflow Monitoring DAG ===
dag_monitoring = DAG(
    'knime_workflow_monitoring',
    default_args=default_args,
    description='Monitor KNIME workflow executions and performance',
    schedule_interval='*/30 * * * *',  # Every 30 minutes
    catchup=False,
    tags=['knime', 'monitoring', 'observability']
)

def monitor_workflow_performance():
    """Monitor KNIME workflow execution performance"""
    # Check for workflow output files and logs
    output_dir = '/tmp/knime_output'
    log_dir = '/tmp/knime_logs'
    
    performance_metrics = {
        'timestamp': datetime.now().isoformat(),
        'workflows_executed': 0,
        'successful_executions': 0,
        'failed_executions': 0,
        'average_execution_time': 0
    }
    
    # Scan for recent workflow outputs
    if os.path.exists(output_dir):
        output_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
        performance_metrics['workflows_executed'] = len(output_files)
        
        # Check file sizes and modification times
        recent_outputs = []
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        for file in output_files:
            file_path = os.path.join(output_dir, file)
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if mod_time > cutoff_time:
                recent_outputs.append({
                    'file': file,
                    'size': os.path.getsize(file_path),
                    'modified': mod_time.isoformat()
                })
        
        performance_metrics['recent_outputs'] = len(recent_outputs)
    
    # Log performance metrics
    logging.info(f"KNIME Performance Metrics: {json.dumps(performance_metrics, indent=2)}")
    
    # Save metrics to file for analysis
    metrics_file = '/tmp/knime_performance_metrics.json'
    with open(metrics_file, 'w') as f:
        json.dump(performance_metrics, f, indent=2)
    
    return performance_metrics

monitoring_task = PythonOperator(
    task_id='monitor_workflow_performance',
    python_callable=monitor_workflow_performance,
    dag=dag_monitoring
)