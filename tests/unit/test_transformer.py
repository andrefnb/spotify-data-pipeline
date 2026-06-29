from datetime import UTC, datetime

import polars as pl

from spotify_pipeline.transformation.transformer import Transformer
from spotify_pipeline.validation.models import PlayedAt


def test_transform_returns_dataframe(sample_played_at: PlayedAt) -> None:
    df = Transformer().transform([sample_played_at])
    assert isinstance(df, pl.DataFrame)
    assert len(df) == 1


def test_transform_deduplicates(sample_played_at: PlayedAt) -> None:
    df = Transformer().transform([sample_played_at, sample_played_at])
    assert len(df) == 1


def test_transform_expected_columns(sample_played_at: PlayedAt) -> None:
    df = Transformer().transform([sample_played_at])
    for col in ("track_id", "track_name", "played_at", "artist_names", "album_name"):
        assert col in df.columns


def test_transform_sorts_descending() -> None:
    from spotify_pipeline.validation.models import Album, Artist, Track

    artist = Artist(id="a1", name="A", uri="spotify:artist:a1")
    album = Album(
        id="al1",
        name="AL",
        release_date="2024-01-01",
        total_tracks=1,
        uri="spotify:album:al1",
    )
    track = Track(
        id="t1",
        name="T",
        duration_ms=1000,
        explicit=False,
        popularity=50,
        uri="spotify:track:t1",
        artists=[artist],
        album=album,
    )

    older = PlayedAt(track=track, played_at=datetime(2024, 1, 1, tzinfo=UTC))
    newer = PlayedAt(track=track, played_at=datetime(2024, 6, 1, tzinfo=UTC))

    df = Transformer().transform([older, newer])
    assert df["played_at"][0] == newer.played_at
