// Talks to the FastAPI backend (/library, /stats, /recommend).
// Types here mirror app/schemas.py and app/api/recommend.py on the backend —
// keep them in sync by hand, there's no shared schema generation yet.

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type BacklogState = "untouched" | "in_progress" | "finished";

export interface GameSummary {
  appid: number;
  name: string;
  playtime_forever_minutes: number;
  state: BacklogState;
  header_image: string;
}

export interface GenreGroup {
  genre: string;
  games: GameSummary[];
}

export interface LibraryResponse {
  genres: GenreGroup[];
}

export interface StateCounts {
  untouched: number;
  in_progress: number;
  finished: number;
}

export interface GenreStats {
  genre: string;
  counts: StateCounts;
}

export interface StatsResponse {
  total: StateCounts;
  by_genre: GenreStats[];
}

export interface RecommendRequest {
  available_time_min: number;
  mood: string;
}

export type PickSource = "library" | "discovery";

export interface RecommendedGame {
  appid: number;
  name: string;
  reason: string;
  source: PickSource;
  header_image: string;
}

export interface RecommendResponse {
  picks: RecommendedGame[];
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(body?.detail ?? response.statusText, response.status);
  }

  return response.json() as Promise<T>;
}

export function getLibrary(): Promise<LibraryResponse> {
  return request<LibraryResponse>("/library");
}

export function getStats(): Promise<StatsResponse> {
  return request<StatsResponse>("/stats");
}

export function getRecommendation(payload: RecommendRequest): Promise<RecommendResponse> {
  return request<RecommendResponse>("/recommend", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
