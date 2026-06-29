from pathlib import Path
from typing import Any

import polars as pl

from spotify_pipeline.config import settings
from spotify_pipeline.logging import log
from spotify_pipeline.validation.models import PlayedAt


class Transformer:
    """Converts validated PlayedAt records into a flat, deduplicated DataFrame."""

    def transform(self, items: list[PlayedAt]) -> pl.DataFrame:
        """Flatten, deduplicate on (track_id, played_at), sort by play time desc."""
        log.info("Starting transformation", record_count=len(items))
        rows = [self._flatten(item) for item in items]
        df = pl.DataFrame(rows)
        df = df.unique(subset=["track_id", "played_at"])
        df = df.sort("played_at", descending=True)
        log.info("Transformation complete", rows=len(df))
        return df

    def _flatten(self, item: PlayedAt) -> dict[str, Any]:
        """Expand a nested PlayedAt into a single flat row dict."""
        track = item.track
        return {
            "played_at": item.played_at,
            "track_id": track.id,
            "track_name": track.name,
            "duration_ms": track.duration_ms,
            "explicit": track.explicit,
            "popularity": track.popularity,
            "track_uri": track.uri,
            "artist_ids": [a.id for a in track.artists],
            "artist_names": [a.name for a in track.artists],
            "album_id": track.album.id,
            "album_name": track.album.name,
            "album_release_date": track.album.release_date,
        }

    def save(self, df: pl.DataFrame) -> Path:
        """Write the DataFrame to data/processed/tracks.parquet and return its path."""
        processed_dir = Path(settings.processed_data_dir)
        processed_dir.mkdir(parents=True, exist_ok=True)
        path = processed_dir / "tracks.parquet"
        df.write_parquet(path)
        log.info("Processed data saved", path=str(path), rows=len(df))
        return path
