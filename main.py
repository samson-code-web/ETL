from prefect import flow , task
from get_api import call_api
from send_to_snowflake import conn_snow

@task(retries=3, retry_delay_seconds=10)
def extract_task():
    print(f"Extraction des données pour la date : ")
    return call_api()

@task
def load_task():
    print("Envoi des données dans le stage Snowflake...")
    return conn_snow()

@flow(name="Pipeline NASA vers Snowflake")
def main_pipeline():
    # Le Flow orchestre le tout
    extract_task()
    load_task()

if __name__ == "__main__":
    main_pipeline()

