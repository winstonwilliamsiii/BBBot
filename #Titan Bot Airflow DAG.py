"""Legacy path retained; production DAG is in workflows/airflow/dags."""

from workflows.airflow.dags.stars_orchestration_dag import dag

__all__ = ["dag"]
