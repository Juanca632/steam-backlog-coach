# steam-backlog-coach

Personal dashboard that analyzes your Steam library:

- **Backlog debt**: how many games you've never started or left half-played, grouped by genre.
- **What to play today**: you tell it how much time you have and what mood you're in, and an LLM
  recommends **only from your real library** (the output is validated against the database, so it
  can't invent games).

Single user, local. No login, no payments. Portfolio / learning project.

## Data sources

| Data | API | Official |
|------|-----|----------|
| Games + playtime | Steam Web API — `GetOwnedGames` | Yes |
| Achievements per game | Steam Web API — `GetPlayerAchievements` | Yes |
| Genre + description | Store API — `appdetails` | No (permanent cache + backoff) |

## Stack

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: React + TypeScript (Vite)
- **AI**: LLM call with the backlog as context (grounding)

## Structure

```
backend/
  app/
    main.py          # FastAPI app + router wiring
    config.py        # settings from environment variables
    db.py            # SQLite engine / session
    models.py        # tables: Game, OwnedGame, AppDetails, SyncState
    schemas.py       # Pydantic response models
    api/
      library.py     # GET /library, GET /stats
      recommend.py   # POST /recommend
    steam/
      web_api.py     # GetOwnedGames, GetPlayerAchievements (official)
      store_api.py   # appdetails (unofficial: cache, backoff, resumable)
      sync.py        # orchestrates the full sync
    backlog/
      classifier.py  # untouched / in_progress / finished
    llm/
      prompt.py      # builds the prompt from backlog + time + mood
      client.py      # LLM call
      validate.py    # validates that the recommended appid exists in the library
  scripts/
    sync.py          # CLI: python -m scripts.sync
  tests/
frontend/            # Vite scaffold (Phase 4)
data/                # the .db file lives here (gitignored)
```

## Development

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in STEAM_API_KEY and STEAM_ID
uvicorn app.main:app --reload

# Library sync (first run is slow due to the appdetails rate limit)
python -m scripts.sync
```
