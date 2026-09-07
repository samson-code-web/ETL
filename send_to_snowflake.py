import os
import logging
import snowflake.connector as sf
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger('etl.send_to_snowflake')

sql_query = """ 
    CREATE TABLE IF NOT EXISTS NASA_DATA(id Int, name VARCHAR(100) , nasa_jpl_url VARCHAR(100) , nasa_date DATE , 
    absolute_magnitude_h Float, km_min Float , km_max Float , m_min Float , m_max Float , 
    miles_min Float , miles_max Float , feet_min Float , feet_max Float ,
    is_potentially_hazardous_asteroid Boolean , kilometers_per_second Float , 
    kilometers_per_hour Float , miles_per_hour Float , astronomical Float , lunar Float ,
    kilometers Float , miles Float , orbiting_body VARCHAR(100), is_sentry_object Boolean );
    """

def conn_snow():
    with sf.connect(user=os.getenv('USER'),password=os.getenv('PASSWORD'),
                account=os.getenv('ACCOUNT'),database=os.getenv('DATABASE'),
                schema=os.getenv('SCHEMA'),warehouse=os.getenv('WAREHOUSE')) as conn:
        with conn.cursor() as cursor:

            cursor.execute("  USE DATABASE SAMSON_STUFF; ")
            cursor.execute("  USE SCHEMA WORK; ")

            logger.info('creating table...')
            cursor.execute(sql_query)

            logger.info("truncation of the table...")
            cursor.execute("TRUNCATE TABLE NASA_DATA;")

            logger.info('putting step...')
            cursor.execute("PUT file://D:/ETL/NASA.parquet @PENDING_DATA OVERWRITE = TRUE ")

            logger.info('copping step...')
            cursor.execute("""
                        COPY INTO NASA_DATA
                        FROM @PENDING_DATA/NASA.parquet
                        FILE_FORMAT = (TYPE = PARQUET)
                        MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE;""")


