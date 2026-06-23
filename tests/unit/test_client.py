import time
from unittest.mock import MagicMock, patch

from spotify_pipeline.client.spotify import SpotifyClient


def _make_client() -> SpotifyClient:
    client = SpotifyClient.__new__(SpotifyClient)
    client._client = MagicMock()
    client._access_token = ""
    client._token_expiry = 0.0
    return client


def test_ensure_token_calls_refresh_when_expired() -> None:
    client = _make_client()
    with patch.object(client, "_refresh_access_token") as mock_refresh:
        client._ensure_token()
        mock_refresh.assert_called_once()


def test_ensure_token_skips_refresh_when_valid() -> None:
    client = _make_client()
    client._token_expiry = time.time() + 1000
    with patch.object(client, "_refresh_access_token") as mock_refresh:
        client._ensure_token()
        mock_refresh.assert_not_called()


def test_refresh_stores_access_token() -> None:
    client = _make_client()
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "tok123", "expires_in": 3600}
    client._client.post.return_value = mock_response

    client._refresh_access_token()

    assert client._access_token == "tok123"
    assert client._token_expiry > time.time()


def test_get_all_recently_played_stops_on_empty_page() -> None:
    client = _make_client()
    client._token_expiry = time.time() + 1000

    with patch.object(client, "get_recently_played") as mock_get:
        mock_get.return_value = {"items": [], "cursors": {}}
        result = client.get_all_recently_played()

    assert result == []
    mock_get.assert_called_once()
