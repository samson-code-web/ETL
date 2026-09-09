import logging
import snowflake.connector as sf
from pathlib import Path

def conn_snow(file_path: str , sf_user: str, sf_password: str, sf_account: str, sf_database: str,sf_schema:str,sf_warehouse: str):
    logger = logging.getLogger(f'etl.{__name__}')

    sql_query = """ 
        CREATE TABLE IF NOT EXISTS NASA_DATA(id Int, name VARCHAR(100) , nasa_jpl_url VARCHAR(100) , nasa_date DATE , 
        absolute_magnitude_h Float, km_min Float , km_max Float , m_min Float , m_max Float , 
        miles_min Float , miles_max Float , feet_min Float , feet_max Float ,
        is_potentially_hazardous_asteroid Boolean , kilometers_per_second Float , 
        kilometers_per_hour Float , miles_per_hour Float , astronomical Float , lunar Float ,
        kilometers Float , miles Float , orbiting_body VARCHAR(100), is_sentry_object Boolean );
        """
    with sf.connect(user=sf_user,password=sf_password,
                account=sf_account,database=sf_database,
                schema=sf_schema,warehouse=sf_warehouse) as conn:
        with conn.cursor() as cursor:

            cursor.execute(f"USE DATABASE {sf_database};")
            cursor.execute(f"USE SCHEMA {sf_schema};")

            logger.info('creating table...')
            cursor.execute(sql_query)

            logger.info("the table is being truncated ...")
            cursor.execute("TRUNCATE TABLE NASA_DATA;")

            logger.info('putting step...')
            safe_path = Path(file_path).as_posix()
            cursor.execute(f"PUT file://{safe_path} @PENDING_DATA OVERWRITE = TRUE ")

            logger.info('copping step...')
            cursor.execute("""
                        COPY INTO NASA_DATA
                        FROM @PENDING_DATA/NASA.parquet
                        FILE_FORMAT = (TYPE = PARQUET)
                        MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;""")


