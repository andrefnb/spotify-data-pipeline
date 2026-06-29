from pathlib import Path

import duckdb

from spotify_pipeline.config import settings
from spotify_pipeline.logging import log


class Warehouse:
    """DuckDB-backed analytics store for processed track plays."""

    def __init__(self) -> None:
        """Open (or create) the DuckDB database and initialise the schema."""
        db_path = Path(settings.duckdb_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect(str(db_path))
        self._init_schema()

    def _init_schema(self) -> None:
        """Create the tracks table if it does not already exist."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                played_at TIMESTAMPTZ PRIMARY KEY,
                track_id VARCHAR NOT NULL,
                track_name VARCHAR,
                duration_ms INTEGER,
                explicit BOOLEAN,
                popularity INTEGER,
                track_uri VARCHAR,
                artist_ids VARCHAR[],
                artist_names VARCHAR[],
                album_id VARCHAR,
                album_name VARCHAR,
                album_release_date VARCHAR
            )
        """)

    def load(self, parquet_path: Path) -> int:
        """Load a Parquet file into DuckDB, skip duplicates, return inserted count."""
        path_str = parquet_path.as_posix()
        before = self._conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]  # type: ignore[index]
        self._conn.execute(f"""
            INSERT INTO tracks
            SELECT * FROM read_parquet('{path_str}')
            ON CONFLICT (played_at) DO NOTHING
        """)
        after = self._conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]  # type: ignore[index]
        inserted = after - before
        log.info("Loaded into DuckDB", rows_inserted=inserted)
        return int(inserted)

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
