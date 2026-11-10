## Production-Grade AWS ETL Pipeline (NASA Neo API)
A resilient, cloud-native Extract, Transform, Load (ETL) data pipeline engineered to ingest Near Earth Object (NEO) telemetry data from the NASA API, transform and structure it using high-performance columnar processing, secure credentials via AWS Secrets Manager, and persist the output to an Amazon S3 data lake.

Designed and deployed with automated orchestration through Prefect, rigorous logging boundaries, and a comprehensive test suite enforcing data contract integrity.

## Architecture & Tech Stack
Language: Python3.14.4

* Orchestration: Prefect 3.x (with automated retries, exponential backoff, and cron scheduling)

* Data Transformation & Processing : Polars (memory-efficient, high-performance columnar operations and nested JSON unnesting)

## Cloud Infrastructure (AWS):

* Amazon S3: Object storage for processed columnar data (.parquet).

* AWS Secrets Manager: Secure, dynamic credential retrieval with cold-start retry handling.

* IAM: Least-privilege execution patterns.

* Testing & Quality Control: pytest, monkeypatch, and boto3 integration testing.

* Networking & HTTP: httpx with strict timeout configurations and comprehensive error handling.

## Pipeline Workflow
* Secret Resolution: On flow startup, the pipeline queries AWS Secrets Manager with built-in retry logic to securely fetch the NASA API key, mitigating infrastructure race conditions during cold starts.

* Extraction & Pagination: Iterates through NASA NEO API endpoints, handling paginated JSON payloads while enforcing strict timeouts and network exception management.

* Columnar Transformation: Flattens deeply nested JSON structures (including estimated diameters, relative velocities, and miss distances across multiple unit measurements) into clean, structured Polars DataFrames, casting dates and projecting exact column schemas.

* Storage Persistence: Writes the transformed dataset locally to an optimized compressed Parquet file (NASA.parquet).

* Cloud Ingestion: Uploads the final Parquet artifact directly into an isolated Amazon S3 bucket (samson-first-etl-bucket-2026). 

## Project Structure
├── main.py                    # Core Prefect flow, task definitions, and AWS Secrets Manager orchestration
├── get_api.py                 # API extraction logic, HTTP client configuration, and Polars transformations
├── uploading_to_s3_bucket.py  # S3 upload handler with boto3 and error management
├── test_get_api.py            # Dual-layer test suite (pytest unit mocking + live AWS integration tests)
├── prefect.yaml               # Prefect deployment configuration and cron schedule
├── .gitignore                 # Repository hygiene rules for logs and local data artifacts
└── .prefectignore             # Prefect artifact exclusion rules

## Testing & Quality Assurance
The codebase includes a dual-layer testing architecture located in test_get_api.py:

* Unit Testing: Uses pytest and monkeypatch to mock httpx client responses, isolating business logic and validating pipeline behavior without external network dependency.

* Integration Testing (test_in_time): Validates live AWS Secrets Manager retrieval and runs contract assertions against real API response schemas to guarantee structural validity.

## Deployment & Scheduling
Managed via Prefect deployments configured in prefect.yaml:

* Work Pool: Local execution pool (my-local-pool)

* Schedule: Automated daily cron execution (30 3 * * * in America/Toronto)