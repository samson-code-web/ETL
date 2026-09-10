import httpx
import time
import logging
import polars as pl
from pathlib import Path

logger = logging.getLogger(f"etl.{__name__}")

def call_api(api_key: str, start_date: str, end_date: str) -> str:
    url = 'https://api.nasa.gov/neo/rest/v1/feed'
    time_secure = httpx.Timeout(15.0, connect=15.0)
    parameter = {'api_key': api_key, 'start_date': start_date, 'end_date': end_date}
    list_api = []

    with httpx.Client() as client:
        i = 0
        total_pages = 50000

        while True:
            try:
                response = client.get(url=url, params=parameter, follow_redirects=True, timeout=time_secure)
                response.raise_for_status()

            except (httpx.HTTPStatusError, httpx.RequestError , httpx.ConnectTimeout , httpx.ReadTimeout) as e:
                logger.exception('%s new attempt in 5 seconds ....',e)
                time.sleep(5)
                break

            data = response.json()

            for data_date, data_info in data.get('near_earth_objects', {}).items():
                df_clean = (
                    pl.DataFrame(data_info)
                    .unnest('estimated_diameter')
                    .with_columns([
                        pl.col("kilometers").struct.rename_fields(["km_min","km_max"]),
                        pl.col("meters").struct.rename_fields(["m_min", "m_max"]),
                        pl.col("miles").struct.rename_fields(["miles_min", "miles_max"]),
                        pl.col("feet").struct.rename_fields(["feet_min","feet_max"]),
                    ])
                    .unnest('kilometers').unnest('meters').unnest('miles').unnest('feet')
                    .explode('close_approach_data', empty_as_null=True)
                    .unnest('close_approach_data')
                    .unnest('relative_velocity')
                    .unnest('miss_distance')
                    .with_columns(pl.lit(data_date).alias("nasa_date"))
                    .with_columns(pl.col("nasa_date").str.to_date())
                    .select([
                        'id', 'name', 'nasa_jpl_url', 'nasa_date',
                        'absolute_magnitude_h', 'km_min', 'km_max', 'm_min', 'm_max',
                        'miles_min', 'miles_max', 'feet_min', 'feet_max', 'is_potentially_hazardous_asteroid',
                        'kilometers_per_second', 'kilometers_per_hour', 'miles_per_hour',
                        'astronomical', 'lunar', 'kilometers', 'miles', 'orbiting_body', 'is_sentry_object'
                    ])
                )
                list_api.append(df_clean)

            link = data.get("links", {}).get("next")

            if link:
                url = link
                parameter = None
                logger.info("Moving to next url")
                i += 1
                logger.info('the value of I became: %s',i)
                time.sleep(1.5)

            else:
                logger.info("All pages have been successfully processed!")
                break

            if i >= total_pages:
                logger.info('all pages have been processed!')
                break

        if list_api:
            logger.info('writing to file')
            df_total = pl.concat(list_api, how='vertical')
            file_path = str(Path(__file__).resolve().parent / 'NASA.parquet')
            df_total.write_parquet(file_path)
            logger.info('file written successfully')
            return file_path
        else:
            logger.error('something went wrong sir')
            return ''