# Spotify Data Pipeline

## Project Overview

ETL pipeline that ingests data from the Spotify API, validates, transforms, and stores it for analytics.

## Stack

- **Ingestion:** Spotify API (OAuth, retries, pagination, rate-limiting)
- **Validation:** Pydantic models
- **Transformation:** Polars
- **Storage:** DuckDB
- **Orchestration:** Prefect
- **Testing:** pytest
- **Logging:** Structured logs (step-level)
- **CI/CD:** GitHub Actions
- **Code quality:** Ruff (lint), Black (format), pre-commit hooks
- **DX:** Makefile (`make install`, `make test`, `make lint`, `make run`)

## Pipeline Flow

```
Spotify API → Extraction → Pydantic Validation → Transformation → DuckDB Warehouse
```

## Layer Responsibilities

### 1. Data Source Integration
- Isolate all API logic in a dedicated client module
- Handle: authentication, retries, pagination, rate-limiting

### 2. Extraction
- Fetch raw data and write timestamped JSON to `data/raw/<date>/recent_tracks.json`

### 3. Validation (Pydantic)
- Validate required fields, types, and datetime parsing
- Catch schema changes early

### 4. Transformation
- Flatten nested JSON, convert timestamps, deduplicate, normalize entities
- Output: `data/processed/tracks.parquet`

### 5. Storage (DuckDB)
- Lightweight, SQL-based, analytics-friendly local warehouse

### 6. Orchestration (Prefect)
- Schedule runs, manage task retries, log step outcomes

### 7. Logging
- Structured, step-level logs: e.g. `INFO Extracted 50 tracks`, `INFO Loaded data into DuckDB`

### 8. Testing
- Unit tests: API client, transformations, Pydantic models
- Integration tests: full pipeline execution
- Mock API responses in unit tests

### 9. Configuration
- No hardcoded secrets — use environment variables
- Load config via Pydantic Settings (`SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`)

### 10. CI/CD (GitHub Actions)
- On push: lint → format check → type check → tests

## Optional Enhancements

- **Incremental loading** — track last ingestion timestamp, only fetch new data
- **Docker** — containerize the pipeline
- **Data quality checks** — Pandera for post-transform validation
- **Dashboard** — Metabase for visualization
