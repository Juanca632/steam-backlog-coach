import { useState } from "react";
import { ApiError, getRecommendation, type RecommendedGame } from "../api/client";

export function WhatToPlay() {
  const [availableTimeMin, setAvailableTimeMin] = useState(30);
  const [mood, setMood] = useState("");
  const [picks, setPicks] = useState<RecommendedGame[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setPicks(null);

    try {
      const response = await getRecommendation({
        available_time_min: availableTimeMin,
        mood: mood.trim() || "anything",
      });
      setPicks(response.picks);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Something went wrong asking for a recommendation.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="recommend-hero">
      <form onSubmit={handleSubmit} className="recommend-form">
        <label className="mood-field">
          What are you in the mood for?
          <input
            type="text"
            value={mood}
            onChange={(e) => setMood(e.target.value)}
            placeholder="e.g. something relaxing, a quick challenge, nostalgic…"
          />
        </label>

        <label className="time-field">
          Minutes to play
          <input
            type="number"
            min={5}
            step={5}
            value={availableTimeMin}
            onChange={(e) => setAvailableTimeMin(Number(e.target.value))}
            required
          />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? "Thinking…" : "Find something to play"}
        </button>
      </form>

      {error && <p className="status status-error">{error}</p>}

      {picks && picks.length > 0 && (
        <div className="game-grid">
          {picks.map((pick) => (
            <article key={pick.appid} className="game-card">
              <img src={pick.header_image} alt={pick.name} loading="lazy" />
              <span className={`card-badge badge-${pick.source}`}>
                {pick.source === "library" ? "From your backlog" : "New for you"}
              </span>
              <div className="card-body">
                <h3>{pick.name}</h3>
                <p>{pick.reason}</p>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
