import httpx
from get_api import call_api
import boto3
import json
from botocore.exceptions import ClientError
import time
import logging

logger = logging.getLogger(f"etl.{__name__}")

def test_call_api(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
    "near_earth_objects": {
        "2026-09-18": [
            {
                "links": {
                    "self": "https://api.nasa.gov/neo/rest/v1/feed"
                },
                "id": "2260277",
                "neo_reference_id": "2260277",
                "name": "260277 (2004 TR12)",
                "nasa_jpl_url": "https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html#/?sstr=2260277",
                "absolute_magnitude_h": 18.27,
                "estimated_diameter": {
                    "kilometers": {
                        "estimated_diameter_min": 0.5895966084,
                        "estimated_diameter_max": 1.3183780956
                    },
                    "meters": {
                        "estimated_diameter_min": 589.5966083829,
                        "estimated_diameter_max": 1318.3780956475
                    },
                    "miles": {
                        "estimated_diameter_min": 0.3663582341,
                        "estimated_diameter_max": 0.8192019157
                    },
                    "feet": {
                        "estimated_diameter_min": 1934.3721366469,
                        "estimated_diameter_max": 4325.3875913241
                    }
                },
                "is_potentially_hazardous_asteroid": False,
                "close_approach_data": [
                    {
                        "close_approach_date": "2026-09-18",
                        "close_approach_date_full": "2026-Sep-18 12:25",
                        "epoch_date_close_approach": 1789734300000,
                        "relative_velocity": {
                            "kilometers_per_second": "15.4495204445",
                            "kilometers_per_hour": "55618.2736003127",
                            "miles_per_hour": "34559.0322823721"
                        },
                        "miss_distance": {
                            "astronomical": "0.2032022987",
                            "lunar": "79.0456941943",
                            "kilometers": "30398631.064623769",
                            "miles": "18888833.4567112522"
                        },
                        "orbiting_body": "Earth"
                    }
                ],
                "is_sentry_object": False
            }
        ]
    }
}
    def mock_get_api(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.Client,"get",mock_get_api)

    value =  call_api("my-fake-api-key","unknown","unknown")

    assert isinstance(value , str)

def test_in_time():
    secrets_client = boto3.client("secretsmanager")
    max_attempts = 10
    delay_seconds = 3

    for attempt in range(1, max_attempts + 1):
        try:
            response = secrets_client.get_secret_value(SecretId="nasa-api-key")
            raw_key = json.loads(response["SecretString"])
            api_key = raw_key.get("api-key", {})
            logger.info("Secret found for the test! Status is active.")
            break

        except ClientError as e:
            error_code = e.response["Error"]["Code"]

            if error_code == "ResourceNotFoundException":
                logger.error(f"Retrying in {delay_seconds}s , secret didn't find ...")
                time.sleep(delay_seconds)
            else:
                raise e
    else:
        raise TimeoutError("Timed out waiting for the secret to be created.")

    parameter = {"api_key": api_key, "start_date": "2020-09-04", "end_date": "2020-09-11"}

    response = httpx.get("https://api.nasa.gov/neo/rest/v1/feed",params=parameter)

    response.raise_for_status()

    data = response.json()

    result = data.get("near_earth_objects",{}).get("2020-09-04",[])[0]

    assert "id" in result
    assert "neo_reference_id" in result
    assert "name" in result
    assert "nasa_jpl_url" in result
    assert "absolute_magnitude_h" in result
    assert "estimated_diameter" in result
    assert "is_potentially_hazardous_asteroid" in result
    assert "is_sentry_object" in result

    assert "estimated_diameter_min" in result.get("estimated_diameter",{}).get("kilometers",{})
    assert "estimated_diameter_max" in result.get("estimated_diameter",{}).get("kilometers",{})
    assert "estimated_diameter_min" in result.get("estimated_diameter",{}).get("meters",{})
    assert "estimated_diameter_max" in result.get("estimated_diameter",{}).get("meters",{})
    assert "estimated_diameter_min" in result.get("estimated_diameter",{}).get("miles",{})
    assert "estimated_diameter_max" in result.get("estimated_diameter",{}).get("miles",{})
    assert "estimated_diameter_min" in result.get("estimated_diameter",{}).get("feet",{})
    assert "estimated_diameter_max" in result.get("estimated_diameter",{}).get("feet",{})

    assert "close_approach_date" in result.get("close_approach_data",[])[0]
    assert "close_approach_date_full" in result.get("close_approach_data",[])[0]
    assert "epoch_date_close_approach" in result.get("close_approach_data",[])[0]
    assert "orbiting_body" in result.get("close_approach_data", [])[0]

    assert "kilometers_per_second" in result.get("close_approach_data",[])[0].get("relative_velocity",{})
    assert "kilometers_per_hour" in result.get("close_approach_data",[])[0].get("relative_velocity",{})
    assert "miles_per_hour" in result.get("close_approach_data",[])[0].get("relative_velocity",{})

    assert "astronomical" in result.get("close_approach_data",[])[0].get("miss_distance",{})
    assert "lunar" in result.get("close_approach_data",[])[0].get("miss_distance",{})
    assert "kilometers" in result.get("close_approach_data",[])[0].get("miss_distance",{})
    assert "miles" in result.get("close_approach_data",[])[0].get("miss_distance",{})

