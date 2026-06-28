FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends git make && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir -e .

ENTRYPOINT ["python", "-m", "spotify_pipeline.orchestration.pipeline"]
