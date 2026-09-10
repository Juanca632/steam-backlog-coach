"""Classifies each game in the library into a backlog state.

States: untouched | in_progress | finished

Signals:
- playtime (OwnedGame.playtime)
- achievement ratio (unlocked / total) when the game has achievements
- genre (a different playtime threshold for roguelike vs long RPG)

The concrete heuristic is defined in Phase 2.
"""
