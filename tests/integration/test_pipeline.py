from pathlib import Path
from unittest.mock import MagicMock

import pytest

from spotify_pipeline.client.spotify import SpotifyClient
from spotify_pipeline.extraction.extractor import Extractor
from spotify_pipeline.storage.warehouse import Warehouse
from spotify_pipeline.transformation.transformer import Transformer
from spotify_pipeline.validation.models import PlayedAt


@pytest.fixture(autouse=True)
def patch_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import spotify_pipeline.config as cfg

    monkeypatch.setattr(cfg.settings, "raw_data_dir", str(tmp_path / "raw"))
    monkeypatch.setattr(cfg.settings, "processed_data_dir", str(tmp_path / "processed"))
    monkeypatch.setattr(cfg.settings, "duckdb_path", str(tmp_path / "test.duckdb"))


def test_full_pipeline(raw_recently_played_item: dict) -> None:
    mock_client = MagicMock(spec=SpotifyClient)
    mock_client.get_all_recently_played.return_value = [raw_recently_played_item]

    items = Extractor(mock_client).extract()
    assert len(items) == 1
    assert isinstance(items[0], PlayedAt)

    transformer = Transformer()
    df = transformer.transform(items)
    parquet_path = transformer.save(df)
    assert parquet_path.exists()

    warehouse = Warehouse()
    try:
        rows_inserted = warehouse.load(parquet_path)
    finally:
        warehouse.close()

    assert rows_inserted == 1


def test_duplicate_runs_are_idempotent(raw_recently_played_item: dict) -> None:
    mock_client = MagicMock(spec=SpotifyClient)
    mock_client.get_all_recently_played.return_value = [raw_recently_played_item]

    items = Extractor(mock_client).extract()
    transformer = Transformer()
    parquet_path = transformer.save(transformer.transform(items))

    warehouse = Warehouse()
    try:
        first_run = warehouse.load(parquet_path)
        second_run = warehouse.load(parquet_path)
    finally:
        warehouse.close()

    assert first_run == 1
    assert second_run == 0
