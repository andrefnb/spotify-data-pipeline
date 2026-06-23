from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class Artist(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    uri: str


class Album(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    release_date: str
    total_tracks: int
    uri: str


class Track(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    duration_ms: int
    explicit: bool
    popularity: int
    uri: str
    artists: list[Artist]
    album: Album


class PlayedAt(BaseModel):
    model_config = ConfigDict(extra="ignore")

    track: Track
    played_at: datetime

    @field_validator("played_at", mode="before")
    @classmethod
    def parse_played_at(cls, v: object) -> datetime:
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v  # type: ignore[return-value]
