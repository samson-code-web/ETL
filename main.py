from prefect import flow, task
from get_api import call_api
from pathlib import Path
from uploading_to_aws_s3_bucket import sending_to_s3
from botocore.exceptions import ClientError
import boto3
import logging
import time
import json

logger = logging.getLogger("etl")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    file_path = Path(__file__).resolve().parent / 'app.log'

    file_handler = logging.FileHandler(str(file_path), mode='a', encoding='utf-8')

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

@task(retries=3, retry_delay_seconds=10)
def extract_task(api_key, start_date, end_date):

    logger.info("working on the call_api function")
    return call_api(api_key=api_key, start_date=start_date, end_date=end_date)

@task(retries=3, retry_delay_seconds=10)
def uploading_to_s3_bucket(file_name , bucket , key):

    logger.info('Sending to S3 bucket...')
    return sending_to_s3(file_name=file_name , bucket=bucket , bucket_key=key)

@flow(name="launching the pipeline")
def pipeline(start_date='2020-09-04',
             end_date='2020-09-11',
             file_name='/home/samson/PycharmProjects/ETL-NASA/NASA.parquet',
             bucket='samson-first-etl-bucket-2026' ,
            key='first/NASA.parquet'):

    secrets_client = boto3.client('secretsmanager', region_name='us-east-2')

    logger.info("Waiting the for secret to become available...")

    max_attempts = 5
    delay_seconds = 2

    for attempt in range(1, max_attempts + 1):
        try:
            response = secrets_client.get_secret_value(SecretId='nasa-api-key')
            raw_key = json.loads(response['SecretString'])
            api_key = raw_key.get('api-key', {})
            logger.info("Secret found! Status is active.")
            break

        except ClientError as e:
            error_code = e.response['Error']['Code']

            if error_code == 'ResourceNotFoundException':
                print(f"Retrying in {delay_seconds}s...")
                time.sleep(delay_seconds)
            else:
                raise e
    else:
        raise TimeoutError("Timed out waiting for the secret to be created.")

    logger.info("Proceeding with the pipeline using the secret...")

    extract_task(api_key, start_date, end_date)
    logger.info('call_api function completed.')

    uploading_to_s3_bucket(file_name= file_name , bucket=bucket , key=key)
    logger.info('file sent successfully ')

