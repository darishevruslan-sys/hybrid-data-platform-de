from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG('2_spark_heavy_analytics', start_date=datetime(2023, 1, 1), schedule_interval=None, catchup=False) as dag:
    run_spark = BashOperator(
        task_id='run_spark_market_analysis',
        bash_command='docker exec spark_master /opt/spark/bin/spark-submit --packages org.apache.hadoop:hadoop-aws:3.3.4 /opt/spark/app/spark_analytics.py'
    )
