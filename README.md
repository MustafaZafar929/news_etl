# News ETL Pipeline

A microservices-based ETL pipeline orchestrated by **Dagster** to ingest, process, and cluster news articles.

## Architecture
- **Ingestion Service**: Scrapes RSS feeds and stores articles in Postgres (Supabase).
- **Processing Service**: Generates embeddings (SentenceTransformer) and clusters articles (DBSCAN).
- **Webserver**: Dagster UI for orchestration and monitoring.

## Prerequisites
- **Docker** and **Docker Compose** installed.
- A **Supabase** database (or any Postgres DB with `pgvector` extension if you want to run vector queries locally, though the code currently handles vector logic with standard arrays/lists in some places, `pgvector` is best for the embedding column).
- A `.env` file in the root directory with:
  ```
  DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/postgres
  ```

## How to Run

1.  **Build and Start Services**
    ```bash
    docker-compose up --build
    ```

2.  **Access Dagster UI**
    Open [http://localhost:3000](http://localhost:3000) in your browser.

3.  **Enable Automation**
    - Navigate to the **Sensors** tab.
    - Toggle **ON** the `trigger_processing_on_ingestion_success` sensor.

4.  **Trigger the Pipeline**
    - Go to **Jobs** -> `ingest_news_job`.
    - Click **Materialize** (or "Launch Run").
    - Once the ingestion job completes successfully, the sensor will automatically trigger the `process_news_job`.

## Development
- **Ingestion Code**: `ingestion/injest.py`
- **Processing Code**: `processing/process.py`
- **Orchestration**: `workspace.yaml` loads the grpc servers.
