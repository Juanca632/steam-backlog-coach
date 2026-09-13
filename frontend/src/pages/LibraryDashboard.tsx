import { useEffect, useState } from "react";
import {
  ApiError,
  getLibrary,
  getStats,
  type BacklogState,
  type LibraryResponse,
  type StatsResponse,
} from "../api/client";

const STATE_LABELS: Record<BacklogState, string> = {
  untouched: "Untouched",
  in_progress: "In progress",
  finished: "Finished",
};

export function LibraryDashboard() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [library, setLibrary] = useState<LibraryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    Promise.all([getStats(), getLibrary()])
      .then(([statsResponse, libraryResponse]) => {
        if (cancelled) return;
        setStats(statsResponse);
        setLibrary(libraryResponse);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : "Failed to load the library.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <p className="status">Loading your backlog…</p>;
  if (error) return <p className="status status-error">{error}</p>;
  if (!stats || !library) return null;

  return (
    <div className="dashboard">
      <section className="totals">
        {(["untouched", "in_progress", "finished"] as const).map((state) => (
          <div key={state} className={`total-card total-${state}`}>
            <span className="total-count">{stats.total[state]}</span>
            <span className="total-label">{STATE_LABELS[state]}</span>
          </div>
        ))}
      </section>

      <section className="genre-groups">
        {library.genres.map((group) => (
          <details key={group.genre} className="genre-group" open>
            <summary>
              {group.genre} <span className="genre-count">({group.games.length})</span>
            </summary>
            <ul className="game-list">
              {group.games.map((game) => (
                <li key={game.appid} className={`game-row state-${game.state}`}>
                  <img className="game-thumb" src={game.header_image} alt="" loading="lazy" />
                  <span className="game-name">{game.name}</span>
                  <span className="game-playtime">
                    {Math.round(game.playtime_forever_minutes / 60)}h
                  </span>
                  <span className="game-state">{STATE_LABELS[game.state]}</span>
                </li>
              ))}
            </ul>
          </details>
        ))}
      </section>
    </div>
  );
}
