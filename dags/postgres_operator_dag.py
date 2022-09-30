'''
Dag executes the process of connecting to a postgres database
and creating two tables.
'''

from datetime import datetime, timedelta, date
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator


default_args = {
    'owner': 'bsmith25',
    'retries': 5,
    'retry_delay': timedelta(minutes = 5)
}

with DAG(
    dag_id = 'postgres_operator_dag_v030',
    default_args = default_args,
    description = 'Dag for executing Postgres operations',
    start_date = datetime(2022, 9, 27, 22, 35),
    schedule_interval = '@daily'
) as dag:
    task1 = PostgresOperator(
        task_id = 'create_songs_table',
        postgres_conn_id = 'postgres_server_2',
        sql = '''CREATE TABLE IF NOT EXISTS playlist_songs (s_id SERIAL PRIMARY KEY,
                date_recorded_in_playlist date, date_added_to_playlist date,
                playlist_id varchar, name varchar, duration float,
                explicit boolean, energy float);'''
    )
    task2 = PostgresOperator(
        task_id = 'create_weather_table',
        postgres_conn_id = 'postgres_server_2',
        sql = '''CREATE TABLE IF NOT EXISTS climate_data (c_id SERIAL PRIMARY KEY,
                _date date, temp float, rain int, wind float);'''
    )

    task1 >> task2

