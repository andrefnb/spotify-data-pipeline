import json
from datetime import date
from pathlib import Path
from typing import Any

from spotify_pipeline.client.spotify import SpotifyClient
from spotify_pipeline.config import settings
from spotify_pipeline.logging import log
from spotify_pipeline.validation.models import PlayedAt


class Extractor:
    def __init__(self, client: SpotifyClient) -> None:
        self._client = client

    def extract(self) -> list[PlayedAt]:
        log.info("Starting extraction")
        raw_items = self._client.get_all_recently_played()
        validated = [PlayedAt.model_validate(item) for item in raw_items]
        self._save_raw(raw_items)
        log.info("Validated records", count=len(validated))
        return validated

    def _save_raw(self, items: list[dict[str, Any]]) -> None:
        today = date.today().isoformat()
        raw_dir = Path(settings.raw_data_dir) / today
        raw_dir.mkdir(parents=True, exist_ok=True)
        path = raw_dir / "recent_tracks.json"
        path.write_text(json.dumps({"items": items}, indent=2, default=str))
        log.info("Raw data saved", path=str(path))
