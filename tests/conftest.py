import os

# Set env vars before the package is imported so Settings() instantiates cleanly
os.environ.setdefault("SPOTIFY_CLIENT_ID", "test_client_id")
os.environ.setdefault("SPOTIFY_CLIENT_SECRET", "test_client_secret")
os.environ.setdefault("SPOTIFY_REFRESH_TOKEN", "test_refresh_token")

from datetime import UTC, datetime

import pytest

from spotify_pipeline.validation.models import Album, Artist, PlayedAt, Track


@pytest.fixture
def sample_artist() -> Artist:
    return Artist(id="artist1", name="Test Artist", uri="spotify:artist:artist1")


@pytest.fixture
def sample_album() -> Album:
    return Album(
        id="album1",
        name="Test Album",
        release_date="2024-01-01",
        total_tracks=10,
        uri="spotify:album:album1",
    )


@pytest.fixture
def sample_track(sample_artist: Artist, sample_album: Album) -> Track:
    return Track(
        id="track1",
        name="Test Track",
        duration_ms=200000,
        explicit=False,
        popularity=75,
        uri="spotify:track:track1",
        artists=[sample_artist],
        album=sample_album,
    )


@pytest.fixture
def sample_played_at(sample_track: Track) -> PlayedAt:
    return PlayedAt(
        track=sample_track,
        played_at=datetime(2024, 3, 12, 10, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def raw_recently_played_item() -> dict:
    return {
        "track": {
            "id": "track1",
            "name": "Test Track",
            "duration_ms": 200000,
            "explicit": False,
            "popularity": 75,
            "uri": "spotify:track:track1",
            "artists": [
                {
                    "id": "artist1",
                    "name": "Test Artist",
                    "uri": "spotify:artist:artist1",
                }
            ],
            "album": {
                "id": "album1",
                "name": "Test Album",
                "release_date": "2024-01-01",
                "total_tracks": 10,
                "uri": "spotify:album:album1",
            },
        },
        "played_at": "2024-03-12T10:00:00Z",
    }
