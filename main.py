from prefect import flow , task
from get_api import call_api
from send_to_snowflake import conn_snow
from pathlib import Path
import logging

logger = logging.getLogger("etl")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    file_path = Path(__file__).resolve().parent / 'app.log'
    file_handler = logging.FileHandler(str(file_path), mode='w', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

@task(retries=3, retry_delay_seconds=10)
def extract_task():
    print(f"working on the call_api function ")
    return call_api()

@task
def load_task():
    print("working on the  conn_snow function...")
    return conn_snow()

@flow(name="launching the pipeline")
def main_pipeline():
    extract_task()
    load_task()

if __name__ == "__main__":
    main_pipeline()

