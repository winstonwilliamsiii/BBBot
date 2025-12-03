#MLFlow_Regression Fundamental DAG
    mlflow>=2.4.1
    import mlflow
    import mlflow.sklearn
    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    
    # Load dataset
    data = pd.read_csv("data/fundamentals_ratios.csv")
    X = data.drop("target", axis=1)
    y = data["target"]
    
    from airflow.operators.python import PythonOperator
from modules.market_data import log_fundamental_ratios, train_and_log_roi_model

log_ratios = PythonOperator(
    task_id='log_ratios_mlflow',
    python_callable=log_fundamental_ratios,
    op_kwargs={'ticker': 'AMZN', 'report_date': '{{ ds }}', 'ratios': '{{ ti.xcom_pull(task_ids="derive_ratios") }}'},
    dag=dag
)

train_roi_model = PythonOperator(
    task_id='train_roi_model',
    python_callable=train_and_log_roi_model,
    op_kwargs={'df': '{{ ti.xcom_pull(task_ids="derive_ratios_df") }}', 'ticker': 'AMZN'},
    dag=dag
)

log_ratios >> train_roi_model
    