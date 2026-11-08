from prefect import flow, task
import boto3
from get_api import call_api
from pathlib import Path
import logging

logger = logging.getLogger("etl")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    file_path = Path(__file__).resolve().parent / 'app.log'

    file_handler = logging.FileHandler(str(file_path), mode='a', encoding='utf-8')

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

sm_client = boto3.client('secretsmanager')

@task(retries=3, retry_delay_seconds=10)
def extract_task(api_key, start_date, end_date):
    logger.info(f"working on the call_api function ")
    return call_api(api_key, start_date, end_date)

@flow(name="launching the pipeline")
def pipeline(start_date='2020-09-04', end_date='2020-09-11'):
    api_key = sm_client.get_secret_value(SecretId="nasa-api-key")

    extract_task(api_key, start_date, end_date)

