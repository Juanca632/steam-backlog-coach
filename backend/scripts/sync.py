"""Sync CLI:  python -m scripts.sync

Runs app.steam.sync.run(). Safe to re-run as many times as needed:
it resumes from the last SyncState and skips whatever is already cached.
"""

from app.steam.sync import run

if __name__ == "__main__":
    run()
