from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    spotify_client_id: str
    spotify_client_secret: str
    spotify_refresh_token: str

    duckdb_path: str = "data/warehouse.duckdb"
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"


settings = Settings()
