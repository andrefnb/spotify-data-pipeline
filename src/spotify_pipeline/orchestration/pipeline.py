from pathlib import Path

from prefect import flow, task

from spotify_pipeline.client.spotify import SpotifyClient
from spotify_pipeline.extraction.extractor import Extractor
from spotify_pipeline.logging import configure_logging, log
from spotify_pipeline.storage.warehouse import Warehouse
from spotify_pipeline.transformation.transformer import Transformer
from spotify_pipeline.validation.models import PlayedAt


@task(retries=3, retry_delay_seconds=10)
def extract() -> list[PlayedAt]:
    """Pull all recently played tracks from Spotify and return validated records."""
    with SpotifyClient() as client:
        return Extractor(client).extract()


@task
def transform(items: list[PlayedAt]) -> str:
    """Flatten and deduplicate records, write Parquet, return the output path."""
    transformer = Transformer()
    df = transformer.transform(items)
    return str(transformer.save(df))


@task
def load(parquet_path: str) -> int:
    """Load the Parquet file into DuckDB and return the number of inserted rows."""
    warehouse = Warehouse()
    try:
        return warehouse.load(Path(parquet_path))
    finally:
        warehouse.close()


@flow(name="spotify-etl")
def run_pipeline() -> None:
    """Orchestrate the full extract → transform → load pipeline."""
    configure_logging()
    log.info("Pipeline started")
    items = extract()
    parquet_path = transform(items)
    rows = load(parquet_path)
    log.info("Pipeline complete", rows_loaded=rows)


if __name__ == "__main__":
    run_pipeline()
