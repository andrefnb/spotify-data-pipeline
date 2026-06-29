# Spotify Data Pipeline

Production-style ETL pipeline that ingests listening history from the Spotify API, validates and transforms the data, and stores it in a local analytics warehouse.

## Pipeline Flow

```
Spotify API → Extraction → Pydantic Validation → Transformation → DuckDB Warehouse
```

Each stage is a discrete Prefect task with retries and structured logging at every step.

## Project Structure

```
spotify-data-pipeline/
├── src/
│   └── spotify_pipeline/
│       ├── client/
│       │   └── spotify.py          # Spotify API client (OAuth, retries, pagination, rate-limiting)
│       ├── extraction/
│       │   └── extractor.py        # Fetches raw tracks, validates with Pydantic, saves raw JSON
│       ├── validation/
│       │   └── models.py           # Pydantic models: PlayedAt → Track → Artist / Album
│       ├── transformation/
│       │   └── transformer.py      # Flattens, deduplicates, sorts, writes Parquet
│       ├── storage/
│       │   └── warehouse.py        # DuckDB loader with upsert-on-conflict
│       ├── orchestration/
│       │   └── pipeline.py         # Prefect flow wiring extract → transform → load
│       ├── config.py               # Pydantic Settings — reads env vars / .env file
│       └── logging.py              # Structured logging via structlog
├── tests/
│   ├── conftest.py                 # Shared fixtures (Artist, Album, Track, PlayedAt)
│   └── unit/
│       ├── test_models.py          # Pydantic validation tests
│       └── test_transformer.py     # Transformation and deduplication tests
├── scripts/
│   └── get_refresh_token.py        # One-time OAuth helper to obtain a refresh token
├── data/
│   ├── raw/<date>/recent_tracks.json   # Timestamped raw API dumps
│   └── processed/tracks.parquet        # Transformed output
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── pyproject.toml
```

## Stack

| Layer | Tool |
|---|---|
| API client | httpx + tenacity |
| Validation | Pydantic v2 |
| Transformation | Polars |
| Storage | DuckDB |
| Orchestration | Prefect |
| Logging | structlog |
| Testing | pytest |
| Linting | Ruff |
| Formatting | Black |
| Type checking | mypy (strict) |
| CI/CD | GitHub Actions |

## Layer Breakdown

### Client — `client/spotify.py`
Handles all Spotify API concerns in isolation: OAuth 2.0 token refresh, automatic retry with exponential backoff (via tenacity) on 429/5xx responses, rate-limit header parsing, and cursor-based pagination for `recently-played`. The access token is cached in memory and refreshed 60 seconds before expiry.

### Extraction — `extraction/extractor.py`
Calls `SpotifyClient.get_all_recently_played()`, feeds each raw item through `PlayedAt.model_validate()`, and persists the raw JSON to `data/raw/<date>/recent_tracks.json` for auditability. Returns a typed `list[PlayedAt]` to the next stage.

### Validation — `validation/models.py`
Four nested Pydantic models with `extra="ignore"` to absorb API schema drift:

```
PlayedAt
  ├── played_at: datetime   (parsed from ISO string / "Z" suffix)
  └── track: Track
        ├── id, name, duration_ms, explicit, popularity, uri
        ├── artists: list[Artist]   (id, name, uri)
        └── album: Album            (id, name, release_date, total_tracks, uri)
```

`PlayedAt` is the only entry point used by the rest of the pipeline; pydantic recursively validates the entire nested structure automatically.

### Transformation — `transformation/transformer.py`
Flattens the nested `PlayedAt` objects into a row-per-play schema, deduplicates on `(track_id, played_at)`, sorts descending by `played_at`, and writes the result to `data/processed/tracks.parquet` via Polars.

Output columns: `played_at`, `track_id`, `track_name`, `duration_ms`, `explicit`, `popularity`, `track_uri`, `artist_ids`, `artist_names`, `album_id`, `album_name`, `album_release_date`.

### Storage — `storage/warehouse.py`
Loads the Parquet file into a local DuckDB database (`data/warehouse.duckdb`) using `INSERT … ON CONFLICT DO NOTHING` on the `played_at` primary key, making loads idempotent. Returns the number of newly inserted rows.

### Orchestration — `orchestration/pipeline.py`
Prefect flow with three tasks:
- `extract` — retries 3 times with 10-second delay
- `transform` — writes Parquet, returns the path
- `load` — reads Parquet into DuckDB, returns row count

### Configuration — `config.py`
Pydantic `BaseSettings` reads from environment variables or a `.env` file. Required variables:

| Variable | Description |
|---|---|
| `SPOTIFY_CLIENT_ID` | Spotify app client ID |
| `SPOTIFY_CLIENT_SECRET` | Spotify app client secret |
| `SPOTIFY_REFRESH_TOKEN` | Long-lived OAuth refresh token |

Optional: `DUCKDB_PATH`, `RAW_DATA_DIR`, `PROCESSED_DATA_DIR`.

### Logging — `logging.py`
Structured, step-level logs via structlog with ISO timestamps. Example output:
```
2024-03-12T10:00:00Z [info] Extracted 50 tracks
2024-03-12T10:00:01Z [info] Transformation complete rows=48
2024-03-12T10:00:01Z [info] Loaded into DuckDB rows_inserted=12
```

## Getting Started

### 1. Obtain a Spotify refresh token
```bash
python scripts/get_refresh_token.py
```
Follow the printed URL, authorise, and paste the redirect URL back. Copy the printed refresh token.

### 2. Configure environment
```bash
cp .env.example .env   # then fill in your credentials
```
```
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SPOTIFY_REFRESH_TOKEN=...
```

### 3. Install and run
```bash
make install   # pip install -e ".[dev]" + pre-commit hooks
make run       # runs the full pipeline once
```

### Docker
```bash
make docker-build
make docker-run
```

## Development

```bash
make test       # pytest
make lint       # ruff check
make format     # ruff format
make typecheck  # mypy (strict)
make clean      # remove __pycache__, .pyc, warehouse.duckdb
```

CI runs lint → format check → type check → tests on every push via GitHub Actions.
