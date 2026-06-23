import base64
import time
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from spotify_pipeline.config import settings
from spotify_pipeline.logging import log

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 500, 502, 503, 504)
    return isinstance(exc, httpx.RequestError)


class SpotifyClient:
    def __init__(self) -> None:
        self._client = httpx.Client(timeout=30)
        self._access_token: str = ""
        self._token_expiry: float = 0.0

    def __enter__(self) -> "SpotifyClient":
        return self

    def __exit__(self, *_: object) -> None:
        self._client.close()

    def _basic_auth(self) -> str:
        credentials = f"{settings.spotify_client_id}:{settings.spotify_client_secret}"
        return base64.b64encode(credentials.encode()).decode()

    def _refresh_access_token(self) -> None:
        response = self._client.post(
            TOKEN_URL,
            headers={"Authorization": f"Basic {self._basic_auth()}"},
            data={
                "grant_type": "refresh_token",
                "refresh_token": settings.spotify_refresh_token,
            },
        )
        response.raise_for_status()
        data = response.json()
        self._access_token = data["access_token"]
        self._token_expiry = time.time() + data["expires_in"] - 60
        log.info("Access token refreshed")

    def _ensure_token(self) -> None:
        if time.time() >= self._token_expiry:
            self._refresh_access_token()

    @retry(
        retry=retry_if_exception(_is_retryable),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        self._ensure_token()
        response = self._client.get(
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {self._access_token}"},
            params=params,
        )
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "5"))
            log.warning("Rate limited", retry_after=retry_after)
            time.sleep(retry_after)
            response.raise_for_status()
        response.raise_for_status()
        return response.json()

    def get_recently_played(
        self, limit: int = 50, after: int | None = None
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit}
        if after is not None:
            params["after"] = after
        return self._get("/me/player/recently-played", params=params)

    def get_all_recently_played(self, max_items: int = 200) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        after: int | None = None

        while len(items) < max_items:
            batch_limit = min(50, max_items - len(items))
            page = self.get_recently_played(limit=batch_limit, after=after)
            page_items = page.get("items", [])
            if not page_items:
                break
            items.extend(page_items)
            cursors = page.get("cursors") or {}
            after_cursor = cursors.get("after")
            if not after_cursor:
                break
            after = int(after_cursor)
            log.info("Fetched page", total=len(items))

        log.info("Extraction complete", total_items=len(items))
        return items
