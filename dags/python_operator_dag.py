'''
This dag automates four python functions, the first two demonstrate
use of xcoms and argument passing between functions. The third,
given the login credentials of a spotify user, pipelines all of the
user's current playlist songs from the spotify API to a postgres table,
and the fourth function pipelines weather data from API to postgres.
'''

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
from datetime import datetime, timedelta
import os
import requests
from psycopg2.extras import execute_values


cid = '<Client ID>'
secret = '<Secret>'
u_num = '<User Number>'
auth_url = 'https://accounts.spotify.com/api/token'
data = {
	'grant_type': 'client_credentials',
	'client_id': cid,
	'client_secret': secret
}
auth_response = requests.post(auth_url, data)
auth_response_data = auth_response.json()
access_token = auth_response_data.get('access_token')
headers = {'Authorization': f'Bearer {access_token}',
			'Content-Type': 'application/json',
            'Accept': 'application/json'}

default_args = {
    'owner': 'bsmith25',
    'retries': 5,
    'retry_delay': timedelta(minutes = 5)
}

def greet(age, ti):
    first_name = ti.xcom_pull(task_ids = 'get_name', key = 'first_name')
    last_name = ti.xcom_pull(task_ids = 'get_name', key = 'last_name')
    return f'Hello, I am {first_name} {last_name} and I am {age} years old'

def get_name(ti):
    ti.xcom_push(key = 'first_name', value = 'Brandon')
    ti.xcom_push(key = 'last_name', value = 'Smith')

def append_tracks(tracks, cols, pl_id):
    date = datetime.now()
    for item in tracks['items']:
        added_at = item['added_at']
        track = item['track']
        cols['date_recorded_in_playlist'].append(date)
        cols['date_added_to_playlist'].append(added_at)
        cols['playlist_id'].append(pl_id)
        cols['name'].append(track['name'])
        cols['duration'].append(round(track['duration_ms'] // 1000 / 60, 2))
        cols['explicit'].append(track['explicit'])
        audio = requests.get(f'https://api.spotify.com/v1/audio-features/{track["id"]}',
            headers = headers).json()
        cols['energy'].append(audio['energy'])
    return cols

def insert_playlist_songs():
    hook = PostgresHook(postgres_conn_id = 'postgres_server_2')
    conn = hook.get_conn()
    curs = conn.cursor()
    cols = {
			'date_recorded_in_playlist': [], 'date_added_to_playlist': [],
			'playlist_id': [], 'name': [], 'duration': [], 'explicit': [],
			'energy': []
			}
    user = requests.get(f'https://api.spotify.com/v1/users/{u_num}',
	    headers = headers).json()
    playlists = requests.get(f'https://api.spotify.com/v1/users/{user["id"]}/playlists',
		headers = headers).json()
    for playlist in playlists['items']:
        pl_id = playlist['id']
        pl = requests.get(f'https://api.spotify.com/v1/playlists/{pl_id}',
			headers = headers).json()
        tracks = pl['tracks']
        cols = append_tracks(tracks, cols, pl_id)
    df = pd.DataFrame(cols).drop_duplicates(subset = ['name'])
    execute_values(curs, '''INSERT INTO playlist_songs (date_recorded_in_playlist,
		date_added_to_playlist, playlist_id, name, duration, explicit, energy) VALUES %s;
    ''', df.values)
    conn.commit()
    print('Playlists Added Successfully')
    curs.close()
    conn.close()
    return True

def insert_weather_data():
    hook = PostgresHook(postgres_conn_id = 'postgres_server_2')
    conn = hook.get_conn()
    curs = conn.cursor()
    city = 'Los Angeles'
    geo_api_key = '<Geo API Key'
    base = 'http://api.openweathermap.org/geo/1.0/direct?q={}&limit=5&appid={}'
    res = requests.get(base.format(city, geo_api_key)).json()[0]
    lat, lon = str(res['lat']), str(res['lon'])
    url = "https://weatherbit-v1-mashape.p.rapidapi.com/current"
    params = {"lat": lat,"lon": lon}
    headers = {
		"X-RapidAPI-Key": "<Rapid API Key>",
		"X-RapidAPI-Host": "<Host>"
	  }
    response = requests.request("GET", url, headers = headers, params = params).json()
    temp = response['data'][0]['temp']
    temp = round(temp * (9/5) + 32, 2)
    rain = response['data'][0]['precip']
    wind = response['data'][0]['wind_spd']
    date = datetime.now()
    day = str(date).split()[0].split('-')[-1]
    curs.execute('INSERT INTO climate_data VALUES %s;', [(date, temp, rain, wind)])
    conn.commit()
    curs.close()
    conn.close()
    print('Weather Data Successfully Added')
    return True


with DAG(
    dag_id = 'python_operator_dag_v072',
    default_args = default_args,
    description = 'Dag for executing Python operations',
    start_date = datetime(2022, 9, 27, 21, 50),
    schedule_interval = '@daily'
) as dag:
    task1 = PythonOperator(
        task_id = 'greet',
        python_callable = greet,
        op_kwargs = {'age': 25}
    )
    task2 = PythonOperator(
        task_id = 'get_name',
        python_callable = get_name
    )
    task3 = PythonOperator(
        task_id = 'insert_playlist_songs',
        python_callable = insert_playlist_songs,
        do_xcom_push = False
    )
    task4 = PythonOperator(
        task_id = 'insert_weather_data',
        python_callable = insert_weather_data,
        do_xcom_push = False
    )

    task2 >> task1 >> task3 >> task4
