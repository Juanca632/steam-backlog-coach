# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Personal dashboard that analyzes one person's Steam library and shows their "backlog debt"
(games never started or left half-played, grouped by genre), plus a "what to play today"
screen where an LLM recommends a game based on available time and mood.

Single user, local, no auth, no payments — this is a deliberate scope decision, not a
temporary shortcut. It is a portfolio / learning project (real API integration, data
modeling, LLM grounding, React frontend). Do not add multi-user, login, or hosting
concerns unless explicitly asked.

All repo content (code, comments, docstrings, commits, docs) is in English. Conversation
with the repo owner may be in Spanish; the artifacts are not.

## Commands

```bash
# Backend (from backend/)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                 # fill STEAM_API_KEY and STEAM_ID
uvicorn app.main:app --reload        # dev server on :8000

python -m scripts.sync               # sync the Steam library into the local DB

pytest                               # all tests
pytest tests/test_foo.py::test_bar   # a single test
```

The frontend is not scaffolded yet (Phase 4): `frontend/` will be
`npm create vite@latest . -- --template react-ts`.

## Architecture

Data flows one direction:

```
Steam APIs  ──(scripts/sync.py, run manually)──>  SQLite (data/backlog.db)  ──>  FastAPI  ──>  React
(source of truth)                                 (local cache + workspace)      (reads DB)     (dashboard)
```

The DB is a **local cache**, never queried by end users and never shared. The web app
only ever reads from it; writes happen only during sync.

### Two Steam APIs, treated very differently

- **Steam Web API** (`app/steam/web_api.py`) — official, API-key'd, reliable.
  `GetOwnedGames` (games + playtime) and `GetPlayerAchievements` (achievement counts).
- **Store API `appdetails`** (`app/steam/store_api.py`) — **unofficial, undocumented,
  aggressively rate-limited** (~200 req / 5 min, returns 429 with no warning). Source of
  genre + description only. Rules: exponential backoff, honor `Retry-After`, and cache
  every response **permanently** in `AppDetails` (genre/description never change). Check
  the cache before every network call.

### The sync must be resumable

`app/steam/sync.py` orchestrates: `GetOwnedGames` → `appdetails` per appid → `GetPlayerAchievements`.
The first full run takes ~10 min for a large library because of the `appdetails` rate
limit. It writes `SyncState` after each step and skips already-cached rows, so it can be
killed and re-run at any point. Preserve this property in any change to the sync path.

### Backlog classification

`app/backlog/classifier.py` labels each owned game `untouched | in_progress | finished`.
Playtime alone is noisy (2h in a roguelike is normal, 2h in an 80h RPG is abandonment),
so the heuristic combines playtime, achievement ratio, and genre-specific thresholds.

### LLM recommendation is grounded and validated

`POST /recommend` (`app/api/recommend.py`):
1. build the candidate backlog from the DB
2. `llm/prompt.py` builds a prompt that lists the real games and requires the model to
   return only appids from that list, as JSON
3. `llm/validate.py` checks every returned appid against the library; on any invalid
   appid, retry the prompt once with the error fed back

The point of step 3 is to make "it cannot invent games" demonstrable, not just asserted.
Keep the validate-and-retry loop when touching this path.

## Config

All settings come from environment / `.env` via `app/config.py` (`pydantic-settings`).
`DATABASE_URL` defaults to `sqlite:///../data/backlog.db`. LLM provider/key/model are
config-driven (`LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL`).

## Roadmap (current position)

- **Phase 0 — Setup**: repo, folder structure, `.env.example` — done. `config.py` and
  `GET /health` were the only working code at this point.
- **Phase 1 — Data ingestion**: done. `models.py` (Game, OwnedGame, AppDetails,
  PlayerAchievements, SyncState), `db.py`, both Steam clients, resumable `sync.py`.
  Verified against real Steam data (`python -m scripts.sync` with real credentials):
  synced a real library, and confirmed the core property — running the sync twice in
  a row hits the rate-limited Store API exactly once total, no duplicate rows.
  `web_api.get_player_achievements` treats HTTP 403 ("Profile is not public" — the
  "game details" privacy setting) the same as HTTP 400 (no achievement schema): both
  return `None` instead of raising.
- **Phase 2 — Backlog logic**: done. `classifier.py` labels each owned game from
  playtime, achievement ratio (when available), and genre-tuned playtime thresholds
  (`LONG_GENRES` / `SHORT_GENRES`) for the games with no achievement schema at all.
  `GET /library` (grouped by genre) and `GET /stats` (totals per state and per genre)
  are wired into `main.py`. Verified with unit tests on the classifier's decision
  table and integration tests against an in-memory SQLite DB, plus a manual check
  against the real synced library.
- **Phase 3 — AI recommendation**: done. `llm/prompt.py` builds a prompt listing every
  candidate backlog game (untouched/in_progress only — finished games are excluded)
  and asks for a JSON reply with two things: a `backlog_pick` appid from that exact
  list, and a few `discovery_picks` (real Steam game titles the player doesn't own,
  by genre affinity). `llm/client.py` dispatches on `settings.llm_provider` to either
  the Anthropic SDK or the Gemini SDK (`google-genai`) — Gemini has a free tier,
  useful for local dev without spending API credits. `POST /recommend` validates
  `backlog_pick.appid` against the real library (`llm/validate.py`), retrying once
  with the error fed back on an invalid appid or malformed JSON before failing with
  502; each `discovery_picks` title is separately resolved against the live Steam
  store catalog (`steam/store_search.py`, unofficial `storesearch` endpoint) and
  silently dropped if it doesn't match a real game — so every returned appid, backlog
  or discovery, is real, never invented, just checked against two different sources.
  Cover art for every returned game (owned or not) is a computed Akamai CDN URL
  (`steam/images.py`), no extra API call needed. Covered by unit tests (prompt,
  validate, provider dispatch) and integration tests with the LLM and store search
  mocked (happy path, discovery resolution/drop, invalid-appid retry, malformed-JSON
  retry, exhausted retries, no-candidates 404). Verified end-to-end against the real
  Gemini API and the real Steam store search. Note: Gemini model names get retired
  fast — the API's 404 error names the current replacement model when that happens.
- **Phase 4 — Frontend**: done. Vite + React + TypeScript (`frontend/`), single page
  (no router — `App.tsx` just stacks the two sections). `pages/WhatToPlay.tsx` is the
  main section: free-text mood + available-time inputs, results shown as a
  Steam/Netflix-style grid of cards with cover art, badged "From your backlog" vs
  "New for you". `pages/LibraryDashboard.tsx` (backlog grouped by genre, with
  thumbnails) sits below it on the same page. `api/client.ts` types mirror the
  backend's Pydantic schemas by hand. Backend has `CORSMiddleware` open for
  `http://localhost:5173` (`app/main.py`). Verified by running both dev servers and
  a live `/recommend` call through the real UI flow.
- **Phase 5 — Polish** (next): README screenshots, sync error handling.

Phase 1 was the fragile core; it's solid now, verified end-to-end (mocked network for
edge cases + one real sync run), so later phases can build on it.
