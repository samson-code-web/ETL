# NASA NeoWS Automated ETL Pipeline

An end-to-end, production-grade ETL pipeline designed to extract near-Earth asteroid data from the NASA NeoWS REST API, transform and structure nested JSON payloads into flattened Parquet datasets using **Polars**, and load them seamlessly into **Snowflake** via **Prefect 3.8** orchestration running headlessly on Linux.

---

## Architecture & Data Flow

```
[ NASA REST API ] 
      (HTTPX + Exponential Backoff & Retry Logic)
[ Extraction & Transformation ] 
        Polars DataFrames (Unnesting, Type Casting, Vectorized Operations)
[ Local Serialization ] 
       High-Compression NASA.parquet File
[ Orchestration (Prefect 3.8) ]
       Secure Secret Blocks Injection & Automated Logs
[ Ingestion & Storage ]
       Snowflake Staging (@PENDING_DATA)
       (COPY INTO with Dynamic Schema Matching)
[ Snowflake Data Warehouse (NASA_DATA Table) ]
```

---

## Key Features & Production Design Standards

* **Idempotent Storage Strategy:** Implements `CREATE TABLE IF NOT EXISTS`, explicit truncation (`TRUNCATE TABLE`), and stage overwrites (`OVERWRITE = TRUE`) to guarantee zero data duplication or partial load corruptions upon pipeline execution.
* **Smart Self-Propagating API Crawler:** Dynamically processes NASA's multi-page pagination by leveraging response-embedded `next` links with parameter reset guards (`parameter = None`), capping loop limits to prevent infinite runtime.
* **High-Performance Transformations (Polars):** Performs nested struct unnesting (`estimated_diameter`, `relative_velocity`, `miss_distance`), list explosions, dynamic date casting, and batch vertical concatenation (`pl.concat`) in memory prior to disk serialization.
* **Resilient Orchestration (Prefect 3.8):** 
  * Granular error propagation (`httpx.HTTPStatusError`, `httpx.RequestError`, timeouts) allowing task-level retries (`retries=3`, `retry_delay_seconds=10`).
  * Parametrized `prefect.yaml` deployment scheduled via cron (`10 23 */3 * *`) set explicitly to `America/Toronto` timezone.
  * Native integration with Prefect `Secret` blocks to eliminate hardcoded credentials in source control.
* **Cross-Platform Compatibility:** Utilizes Python's `pathlib.Path.as_posix()` to normalize file paths across Windows and Linux environments, preventing SQL syntax escaping issues during Snowflake `PUT` operations.

---

## Tech Stack & Tooling

| Component | Technology | Role / Usage |
| :--- | :--- | :--- |
| **Language** | Python 3.14+ | Pipeline development & data processing |
| **Data Engine** | Polars | Vectorized transformation, unnesting & Parquet generation |
| **HTTP Client** | HTTPX | Asynchronous-capable HTTP transport with timeout enforcement |
| **Orchestrator** | Prefect 3.8 | Flow/Task orchestration, retry management & scheduled triggers |
| **Data Warehouse** | Snowflake-connector-python | Target cloud data warehouse for analytics workloads |
| **Storage Format** | Apache Parquet | Columnar file serialization prior to Snowflake ingestion |
| **OS / Runtime** | Remote Linux (Ubuntu/Debian) | Headless server execution via system agents |

---

## Repository Structure

```

get_api.py # API Extraction, Polars cleaning, and Parquet serialization logic
send_to_snowflake.py # Snowflake staging, table initialization, and COPY INTO ingestion
main.py # Main Prefect flow & task definitions with logger configuration
prefect.yaml # Prefect deployment configuration, entrypoint, and schedule settings
app.log # Production execution logs (auto-generated at runtime)
README.md # Project documentation
```

---

## Pipeline Execution Walkthrough

### 1. Data Extraction (`get_api.py`)
* Connects to NASA NeoWS feed using `httpx.Client()` configured with standard timeouts.
* Traverses paginated REST responses, extracting nested object schemas.
* Normalizes data structures into flat Polars DataFrames with explicit column typing:
  * Renames struct fields (`km_min`, `km_max`, `m_min`, `m_max`, etc.).
  * Casts `nasa_date` strings to native `pl.Date` types.
  * Explodes `close_approach_data` array objects.
* Concatenates DataFrames vertically (`pl.concat(..., how='vertical')`) and writes to `NASA.parquet`.

### 2. Snowflake Ingestion (`send_to_snowflake.py`)
* Establishes a secure connection using parameters retrieved from Prefect secret blocks.
* Ensures the target table `NASA_DATA` exists with appropriate data types (`INT`, `VARCHAR`, `DATE`, `FLOAT`, `BOOLEAN`).
* Truncates existing staging tables to maintain full pipeline idempotency.
* Uploads the local Parquet file to the internal stage `@PENDING_DATA` using standard POSIX pathing.
* Executes `COPY INTO NASA_DATA` with `MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE`.

### 3. Orchestration & Scheduling (`main.py` + `prefect.yaml`)
* Configures custom file logging to `app.log` without handler duplication.
* Wraps extraction and loading functions inside Prefect `@task` decorators with configured retry intervals.
* Schedules automatic flow execution every 3 days at 23:10 Ottawa time (`America/Toronto`).

---

## Getting Started

### Prerequisites

* Python 3.14+
* A valid NASA API Key ([api.nasa.gov](https://api.nasa.gov/))
* Active Snowflake Account (Warehouse, Database, Schema, User with write privileges)
* Prefect 3.x instance / cloud account

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/nasa-snowflake-etl.git
   cd nasa-snowflake-etl
   ```

2. **Install dependencies:**
   ```bash
   pip install polars httpx prefect snowflake-connector-python
   ```

3. **Configure Prefect Secret Blocks:**
   Create the following `Secret` blocks in your Prefect UI or via CLI:
   * `api-key`: Your NASA API key
   * `sf-user`: Snowflake username
   * `sf-password`: Snowflake password
   * `sf-account`: Snowflake account identifier
   * `sf-database`: Target database name
   * `sf-schema`: Target schema name
   * `sf-warehouse`: Target compute warehouse name

4. **Deploy and run the pipeline:**
   ```bash
   # Execute a one-off run locally or on server
   python main.py

   # Deploy using Prefect YAML
   prefect deploy
   ```

---

## Error Handling & Logging

* **Custom Logging:** All events (HTTP requests, URL updates, DataFrame unnesting, file IO, and Snowflake status) are logged cleanly to `app.log`.
* **Exception Handling:** Explicit exception tuple catching (`httpx.HTTPStatusError`, `httpx.RequestError`, `httpx.ConnectTimeout`, `httpx.ReadTimeout`) ensures network fluctuations trigger Prefect retries without crashing the server process silently.
* **Failure Guard:** Unsuccessful API queries automatically log an explicit error and abort the Snowflake ingestion step using a `ValueError` guard.

---

## Author & Acknowledgments

* **Data Engineer:** Junior Data Engineer Portfolio Project (Ottawa, ON)
* **Data Source:** [NASA Open Data APIs - NeoWS Feed](https://api.nasa.gov/)
