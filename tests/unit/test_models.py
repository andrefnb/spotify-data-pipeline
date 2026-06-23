from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from spotify_pipeline.validation.models import PlayedAt


def test_played_at_parses_utc_datetime(raw_recently_played_item: dict) -> None:
    played = PlayedAt.model_validate(raw_recently_played_item)
    assert played.played_at == datetime(2024, 3, 12, 10, 0, 0, tzinfo=timezone.utc)


def test_played_at_requires_track(raw_recently_played_item: dict) -> None:
    del raw_recently_played_item["track"]
    with pytest.raises(ValidationError):
        PlayedAt.model_validate(raw_recently_played_item)


def test_played_at_requires_played_at(raw_recently_played_item: dict) -> None:
    del raw_recently_played_item["played_at"]
    with pytest.raises(ValidationError):
        PlayedAt.model_validate(raw_recently_played_item)


def test_track_has_correct_artist(raw_recently_played_item: dict) -> None:
    played = PlayedAt.model_validate(raw_recently_played_item)
    assert len(played.track.artists) == 1
    assert played.track.artists[0].name == "Test Artist"


def test_extra_fields_are_ignored(raw_recently_played_item: dict) -> None:
    raw_recently_played_item["context"] = None
    raw_recently_played_item["track"]["preview_url"] = "https://example.com/preview"
    played = PlayedAt.model_validate(raw_recently_played_item)
    assert played.track.name == "Test Track"
