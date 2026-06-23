"""
Run once to get your Spotify refresh token.

Usage:
    python scripts/get_refresh_token.py

Setup:
    1. In your Spotify app dashboard, add this redirect URI:
       https://httpbin.org/get
    2. Run this script — it opens the Spotify login page.
    3. After authorizing, httpbin.org shows a JSON page.
       Find the "code" value and paste it here.

Requires SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env (or environment).
"""

import os
import urllib.parse
import webbrowser
from base64 import b64encode

import httpx
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]
REDIRECT_URI = "https://httpbin.org/get"
SCOPE = "user-read-recently-played"


def main() -> None:
    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
        f"&scope={urllib.parse.quote(SCOPE)}"
    )

    print("Opening Spotify login in your browser...")
    print()
    print("After you log in and approve, you'll land on a page that looks like:")
    print('  { "args": { "code": "AQD3..." }, ... }')
    print()
    print("Copy just the code value and paste it below.")
    print()
    webbrowser.open(auth_url)

    code = input("Paste the code here: ").strip()
    if not code:
        print("No code entered. Aborting.")
        return

    credentials = b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    response = httpx.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {credentials}"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
    )
    response.raise_for_status()
    data = response.json()

    refresh_token = data.get("refresh_token")
    if refresh_token:
        print(f"\nSPOTIFY_REFRESH_TOKEN={refresh_token}")
        print("\nAdd the line above to your .env file.")
    else:
        print("No refresh token in response:", data)


if __name__ == "__main__":
    main()
