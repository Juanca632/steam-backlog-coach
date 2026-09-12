"""Store API `appdetails` client (UNOFFICIAL).

Critical points:
- aggressive rate limit (~200 requests / 5 min, returns 429 with no warning)
- exponential backoff + honor Retry-After
- everything fetched is cached PERMANENTLY in AppDetails (genre/description never change)
- get_app_details(appid) checks the cache before hitting the network
"""

import time

import httpx
from sqlalchemy.orm import Session

from app.models import AppDetails

BASE_URL = "https://store.steampowered.com/api/appdetails"
TIMEOUT = 10.0
MAX_RETRIES = 5
BACKOFF_BASE_SECONDS = 2.0


def get_app_details(db: Session, appid: int) -> AppDetails:
    """Return the cached AppDetails row for `appid`, fetching it once if missing.

    Genre and description never change once a game ships, so a cache hit
    never touches the network. This is what makes the sync resumable
    despite the Store API's rate limit: killing and re-running it only
    ever pays the network cost for appids that never got a row here —
    success or "unavailable" alike, both get cached (see `_fetch`).

    Commits immediately so the cache write survives even if the process
    is killed right after this call returns.
    """
    cached = db.get(AppDetails, appid)
    if cached is not None:
        return cached

    genres, description = _fetch(appid)

    details = AppDetails(appid=appid, genres=genres, description=description)
    db.add(details)
    db.commit()
    db.refresh(details)
    return details


def _fetch(appid: int) -> tuple[str, str]:
    """Hit the Store API for one appid, retrying on 429 with backoff.

    Returns `("", "")` if Steam reports the app as unavailable (delisted,
    region-locked, etc.) — that's a real, final answer worth caching, not
    an error to retry.
    """
    for attempt in range(MAX_RETRIES):
        response = httpx.get(BASE_URL, params={"appids": appid}, timeout=TIMEOUT)

        if response.status_code == 429:
            time.sleep(_retry_delay(response, attempt))
            continue

        response.raise_for_status()
        payload = response.json().get(str(appid), {})
        if not payload.get("success"):
            return "", ""

        data = payload.get("data", {})
        genres = ", ".join(g["description"] for g in data.get("genres", []))
        description = data.get("short_description", "")
        return genres, description

    raise RuntimeError(
        f"appdetails rate limit never cleared for appid {appid} after {MAX_RETRIES} retries"
    )


def _retry_delay(response: httpx.Response, attempt: int) -> float:
    """Honor `Retry-After` when Steam sends it; otherwise back off exponentially."""
    retry_after = response.headers.get("Retry-After")
    if retry_after is not None:
        return float(retry_after)
    return BACKOFF_BASE_SECONDS * (2**attempt)
