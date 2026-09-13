"""Recommendation endpoint.

POST /recommend  { available_time_min: int, mood: str }
  1. build the candidate backlog from the DB
  2. build the prompt (llm/prompt.py) and call the LLM (llm/client.py)
  3. validate that the returned appid(s) exist in the library (llm/validate.py);
     if not, retry once.

Only untouched/in_progress games are offered — recommending an already
finished game defeats the point of a backlog coach.
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

router = APIRouter()

MAX_ATTEMPTS = 2


class RecommendRequest(BaseModel):
    available_time_min: int
    mood: str


class RecommendResponse(BaseModel):
    appid: int
    name: str
    reason: str


@router.post("/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest, db: Session = Depends(get_db)) -> RecommendResponse:
    candidates = _build_candidates(db)
    if not candidates:
        raise HTTPException(status_code=404, detail="No backlog games to recommend from.")

    games_by_appid = {c.appid: c for c in candidates}
    known_appids = set(games_by_appid)

    error_feedback = ""
    for _ in range(MAX_ATTEMPTS):
        prompt = build_prompt(candidates, request.available_time_min, request.mood)
        raw = llm_client.complete(prompt + error_feedback)

        try:
            payload = json.loads(raw)
            appid = int(payload["appid"])
            reason = str(payload.get("reason", ""))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            error_feedback = (
                "\n\nYour previous reply was not valid JSON. Reply with ONLY the JSON object."
            )
            continue

        valid, invalid = validate_recommendation([appid], known_appids)
        if valid:
            game = games_by_appid[valid[0]]
            return RecommendResponse(appid=game.appid, name=game.name, reason=reason)

        error_feedback = (
            f"\n\nYour previous reply used appid {invalid[0]}, which is NOT in the "
            "candidate list above. Pick an appid strictly from that list."
        )

    raise HTTPException(
        status_code=502,
        detail="LLM did not return a valid appid from the backlog after retrying.",
    )


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
