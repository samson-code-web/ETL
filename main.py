from prefect import flow, task
from prefect.blocks.system import Secret
from get_api import call_api
from send_to_snowflake import conn_snow
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

@task(retries=3, retry_delay_seconds=10)
def extract_task(api_key, start_date, end_date):
    logging.info(f"working on the call_api function ")
    return call_api(api_key, start_date, end_date)


@task
def load_task(file, sf_user, sf_password, sf_account, sf_database, sf_schema, sf_warehouse):
    logging.info("working on the conn_snow function...")
    return conn_snow(file, sf_user, sf_password, sf_account, sf_database, sf_schema, sf_warehouse)


@flow(name="launching the pipeline")
def pipeline(start_date='2022-09-04', end_date='2022-09-11'):
    # Récupération des secrets
    api_key = Secret.load("api-key").get()
    sf_user = Secret.load('sf-user').get()
    sf_password = Secret.load("sf-password").get()
    sf_account = Secret.load('sf-account').get()
    sf_database = Secret.load('sf-database').get()
    sf_schema = Secret.load('sf-schema').get()
    sf_warehouse = Secret.load('sf-warehouse').get()

    file = extract_task(api_key, start_date, end_date)

    if file:
        load_task(file, sf_user, sf_password, sf_account, sf_database, sf_schema, sf_warehouse)

if __name__ == "__main__":
    pipeline()


