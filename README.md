#  NASA Asteroids (NEO) ETL Pipeline

An automated, robust Data Engineering ETL pipeline that extracts Near Earth Object (NEO) data from the NASA API, processes highly nested JSON structures, and loads the optimized data into a Snowflake Data Warehouse. The entire workflow is orchestrated using Prefect.

##  Tech Stack

* **Language:** Python 3.14
* **Orchestration:** Prefect
* **Data Processing:** Polars (Chosen for high-performance handling of nested data structures)
* **Data Warehouse:** Snowflake
* **Storage Format:** Parquet

##  Pipeline Architecture

1. **Extract:** Connects to the NASA REST API (`NeoWs`) with resilient timeout management, fetching paginated data within a specified date range.
2. **Transform:** Utilizes Polars to aggressively unnest and explode deeply layered JSON data (e.g., estimated diameters, close approach data) into a clean, flat columnar structure before writing it to a Parquet file.
3. **Load:** Connects to Snowflake, dynamically creates the target table (`NASA_DATA`), stages the Parquet file using a `PUT` command, and executes a `COPY INTO` command for fast, bulk ingestion.

##  Setup & Execution

### Prerequisites
Ensure you have a Python virtual environment configured and the following dependencies installed:
`pip install prefect polars httpx snowflake-connector-python`

### Configuration
The pipeline relies on Prefect Secret blocks for secure credential management. You must create the following blocks in your Prefect UI/Server before running the pipeline:
* `api-key`:  NASA API Key
* `sf-user`, `sf-password`, `sf-account`: Snowflake connection credentials
* `sf-database`, `sf-schema`, `sf-warehouse`: Snowflake environment targets

