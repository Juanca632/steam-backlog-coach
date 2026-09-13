"""Recommendation endpoint.

POST /recommend  { available_time_min: int, mood: str }
  1. build the candidate backlog from the DB
  2. build the prompt (llm/prompt.py) and call the LLM (llm/client.py)
  3. validate the backlog pick's appid against the library (llm/validate.py);
     retry once on an invalid appid or malformed JSON
  4. resolve each discovery pick's title against the real Steam catalog
     (steam/store_search.py); silently drop any that don't resolve

Every game returned — backlog or discovery — is a real Steam appid, never
invented: the backlog pick is checked against the owned library, and
discovery picks are checked against the live Steam store catalog. Only
untouched/in_progress games are offered as the backlog pick — recommending
an already finished game defeats the point of a backlog coach.
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.backlog.classifier import classify
from app.db import get_db
from app.llm import client as llm_client
from app.llm.prompt import Candidate, build_prompt
from app.llm.validate import validate_recommendation
from app.models import Game
from app.steam import store_search
from app.steam.images import header_image_url

router = APIRouter()

MAX_ATTEMPTS = 2
DISCOVERY_LIMIT = 3


class RecommendRequest(BaseModel):
    available_time_min: int
    mood: str


class RecommendedGame(BaseModel):
    appid: int
    name: str
    reason: str
    source: str  # "library" | "discovery"
    header_image: str


class RecommendResponse(BaseModel):
    picks: list[RecommendedGame]


@router.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest, db: Session = Depends(get_db)) -> RecommendResponse:
    candidates = _build_candidates(db)
    if not candidates:
        raise HTTPException(status_code=404, detail="No backlog games to recommend from.")

    games_by_appid = {c.appid: c for c in candidates}
    known_appids = set(games_by_appid)

    backlog_pick, discovery_titles = _ask_llm(candidates, request, known_appids)

    picks = [
        RecommendedGame(
            appid=backlog_pick["appid"],
            name=games_by_appid[backlog_pick["appid"]].name,
            reason=backlog_pick["reason"],
            source="library",
            header_image=header_image_url(backlog_pick["appid"]),
        )
    ]
    picks.extend(_resolve_discovery_picks(discovery_titles))

    return RecommendResponse(picks=picks)


def _ask_llm(
    candidates: list[Candidate], request: RecommendRequest, known_appids: set[int]
) -> tuple[dict, list[dict]]:
    """Call the LLM, validating only the backlog pick; retries once on a miss."""
    error_feedback = ""
    for _ in range(MAX_ATTEMPTS):
        prompt = build_prompt(candidates, request.available_time_min, request.mood)
        raw = llm_client.complete(prompt + error_feedback)

        try:
            payload = json.loads(raw)
            appid = int(payload["backlog_pick"]["appid"])
            reason = str(payload["backlog_pick"].get("reason", ""))
            discovery = payload.get("discovery_picks", [])
            if not isinstance(discovery, list):
                discovery = []
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            error_feedback = (
                "\n\nYour previous reply was not valid JSON in the required shape. "
                "Reply with ONLY the JSON object described above."
            )
            continue

        valid, invalid = validate_recommendation([appid], known_appids)
        if valid:
            return {"appid": valid[0], "reason": reason}, discovery

        error_feedback = (
            f"\n\nYour previous backlog_pick used appid {invalid[0]}, which is NOT in "
            "the candidate list above. Pick an appid strictly from that list."
        )

    raise HTTPException(
        status_code=502,
        detail="LLM did not return a valid backlog appid after retrying.",
    )


def _resolve_discovery_picks(discovery_titles: list) -> list[RecommendedGame]:
    """Resolve each suggested title against the real Steam catalog, dropping misses."""
    picks = []
    for entry in discovery_titles[:DISCOVERY_LIMIT]:
        if not isinstance(entry, dict):
            continue
        title = str(entry.get("title", "")).strip()
        if not title:
            continue

        resolved = store_search.find_game_by_title(title)
        if resolved is None:
            continue

        picks.append(
            RecommendedGame(
                appid=resolved["appid"],
                name=resolved["name"],
                reason=str(entry.get("reason", "")),
                source="discovery",
                header_image=header_image_url(resolved["appid"]),
            )
        )
    return picks


def _build_candidates(db: Session) -> list[Candidate]:
    """The recommendable backlog: owned games that aren't already finished."""
    candidates = []
    for game in db.query(Game).all():
        if game.owned is None:
            continue
        state = classify(game.owned, game.details, game.achievements)
        if state == "finished":
            continue
        candidates.append(
            Candidate(
                appid=game.appid,
                name=game.name,
                genre=game.details.genres if game.details else "",
                playtime_minutes=game.owned.playtime_forever_minutes,
                state=state,
            )
        )
    return candidates
