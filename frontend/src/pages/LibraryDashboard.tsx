import { useEffect, useMemo, useState } from "react";
import {
  ApiError,
  getLibrary,
  getStats,
  type BacklogState,
  type GameSummary,
  type LibraryResponse,
  type StatsResponse,
} from "../api/client";

const STATE_LABELS: Record<BacklogState, string> = {
  untouched: "Untouched",
  in_progress: "In progress",
  finished: "Finished",
};

const ALL_GENRES = "All";

export function LibraryDashboard() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [library, setLibrary] = useState<LibraryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedGenre, setSelectedGenre] = useState<string>(ALL_GENRES);

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

  const allGames = useMemo(() => {
    if (!library) return [];
    const byAppid = new Map<number, GameSummary>();
    for (const group of library.genres) {
      for (const game of group.games) byAppid.set(game.appid, game);
    }
    return Array.from(byAppid.values()).sort((a, b) => a.name.localeCompare(b.name));
  }, [library]);

  const visibleGames = useMemo(() => {
    if (selectedGenre === ALL_GENRES) return allGames;
    const group = library?.genres.find((g) => g.genre === selectedGenre);
    return group?.games ?? [];
  }, [allGames, library, selectedGenre]);

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

      <div className="genre-filter">
        <button
          type="button"
          className={selectedGenre === ALL_GENRES ? "genre-pill active" : "genre-pill"}
          onClick={() => setSelectedGenre(ALL_GENRES)}
        >
          {ALL_GENRES} <span className="genre-count">({allGames.length})</span>
        </button>
        {library.genres.map((group) => (
          <button
            key={group.genre}
            type="button"
            className={selectedGenre === group.genre ? "genre-pill active" : "genre-pill"}
            onClick={() => setSelectedGenre(group.genre)}
          >
            {group.genre} <span className="genre-count">({group.games.length})</span>
          </button>
        ))}
      </div>

      <div className="game-grid">
        {visibleGames.map((game) => (
          <article key={game.appid} className="game-card">
            <img src={game.header_image} alt={game.name} loading="lazy" />
            <span className={`card-badge badge-state-${game.state}`}>
              {STATE_LABELS[game.state]}
            </span>
            <div className="card-body">
              <h3>{game.name}</h3>
              <p className="game-playtime">
                {Math.round(game.playtime_forever_minutes / 60)}h played
              </p>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
