from datetime import datetime, timedelta

# Operators; we need this to operate!
from airflow.operators.bash import BashOperator

# The DAG object; we'll need this to instantiate a DAG
from airflow import DAG

default_args = {
    "depends_on_past": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "steam_ingestion_dag",
    default_args=default_args,
    description="Ingest the top 100 games from the Steam API to Azure",
    schedule_interval=timedelta(hours=8),  # Cada 8 horas
    start_date=datetime(2024, 1, 1), 
    catchup=False,
    tags=["steam_project"],
) as dag:
    
    t1 = BashOperator(
        task_id="execute_python_script",
        bash_command="cd /opt/airflow && python dags/scripts/ingest_steam_data.py",
    )
