'''
Simple dag concept automating the execution of three Bash commands,
beginning with task 1 running on its own, and tasks 2 and 3 downstream
from task 1 running concurrently.
'''

from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'bsmith25',
    'retries': 5,
    'retry_delay': timedelta(minutes = 5)
}

with DAG(
    dag_id = 'bash_operator_dag_v04',
    default_args = default_args,
    description = 'Dag for executing Bash operations',
    start_date = datetime(2022, 9, 12, 20, 35),
    schedule_interval = '@daily'
) as dag:
    task1 = BashOperator(
        task_id = 'first_task',
        bash_command = 'echo this is the first task'
    )
    task2 = BashOperator(
        task_id = 'second_task',
        bash_command = 'echo this is the second task, running after task1'
    )
    task3 = BashOperator(
        task_id = 'third_task',
        bash_command = 'echo task3, running after task1 and at the same time as task2'
    )
    
    task1 >> [task2, task3]