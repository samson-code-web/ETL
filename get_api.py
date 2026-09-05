import httpx
import os
import time
from dotenv import load_dotenv
import polars as pl

load_dotenv()

param = {'api_key': os.getenv('API_KEY'),
         'start_date' : '2026-09-04',
         'end_date' : '2026-09-11',
         }

def call_api():
    url = 'https://api.nasa.gov/neo/rest/v1/feed'
    time_secure = httpx.Timeout(15.0, connect=15.0)
    final_params = param
    list_api = []

    with httpx.Client() as client:
        i = 0
        total_pages = 10000

        while True:
            try:
                response = client.get(url=url, params=final_params, follow_redirects=True, timeout=time_secure)
                response.raise_for_status()

            except (httpx.HTTPStatusError, httpx.RequestError , httpx.ConnectTimeout , httpx.ReadTimeout) as e:
                print(f'{e} new attempt in 5 seconds ....')
                time.sleep(5)
                continue

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
                final_params = None
                print(f"Moving to next url: {url}")
                i += 1
                print(i)
                time.sleep(1.5)
            else:
                print("All pages have been successfully processed!")
                break

            if i >= total_pages:
                print('all pages have been processed!')
                break

        if list_api:
            print('writing to file')
            df_total = pl.concat(list_api, how='vertical')
            df_total.write_parquet("NASA.parquet")
            print('file written successfully')

        else:
            print('something went wrong sir')

call_api()

# add logging and prefect