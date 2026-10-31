"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import GameCard from "@/components/GameCard";
import { api, ApiError } from "@/lib/api";
import type { Game, GameListResponse } from "@/lib/types";

type RecommendationResponse = { source: { type: string; title?: string }; games: Game[] };

export default function RecommendationsPage() {
  const [mode, setMode] = useState<"description" | "game">("description");
  const [query, setQuery] = useState("");
  const [referenceGame, setReferenceGame] = useState("");
  const [games, setGames] = useState<Game[]>([]);
  const [results, setResults] = useState<Game[]>([]);
  const [source, setSource] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingGames, setLoadingGames] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    async function loadGames() {
      setLoadingGames(true);
      try {
        const first = await api<GameListResponse>("/api/games?page=1&page_size=48&sort=title_asc");
        let all = first.games;
        if (first.pages > 1) {
          const rest = await Promise.all(Array.from({ length: first.pages - 1 }, (_, i) => api<GameListResponse>(`/api/games?page=${i + 2}&page_size=48&sort=title_asc`)));
          all = all.concat(...rest.map((p) => p.games));
        }
        if (alive) {
          setGames(all);
          const params = new URLSearchParams(window.location.search);
          if (params.get("game_id")) { setMode("game"); setReferenceGame(params.get("game_id") || ""); }
        }
      } catch (e) { if (alive) setError(e instanceof Error ? e.message : "Could not load the catalogue."); }
      finally { if (alive) setLoadingGames(false); }
    }
    void loadGames();
    return () => { alive = false; };
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLoading(true); setError(""); setResults([]); setSource("");
    try {
      const path = mode === "game" ? `/api/recommendations?game_id=${encodeURIComponent(referenceGame)}&limit=9` : `/api/recommendations?q=${encodeURIComponent(query.trim())}&limit=9`;
      const data = await api<RecommendationResponse>(path);
      setResults(data.games); setSource(mode === "game" ? `games similar to ${data.source.title || "your selection"}` : "your description");
    } catch (e) { setError(e instanceof ApiError ? e.message : "Could not generate recommendations."); }
    finally { setLoading(false); }
  }

  return (
    <>
      <div className="page-heading"><div className="eyebrow">Powered by PostgreSQL + pgvector</div><h1 className="page-title">A little more your kind of game.</h1><p>Describe what you love or choose a game as a starting point. Steamish compares text embeddings to retrieve titles with similar content—not a promise that you&apos;ll enjoy them.</p></div>
      <div className="two-column">
        <section className="content-panel">
          <div className="section-kicker">Find your next obsession</div><h2 style={{ fontFamily: "Space Grotesk", margin: "8px 0 19px" }}>Tune your discovery</h2>
          <div className="genre-strip" style={{ margin: "0 0 20px" }}><button className={`genre-chip ${mode === "description" ? "selected" : ""}`} onClick={() => setMode("description")}>Describe my taste</button><button className={`genre-chip ${mode === "game" ? "selected" : ""}`} onClick={() => setMode("game")}>Start from a game</button></div>
          <form onSubmit={submit}>
            {mode === "description" ? <div className="form-field"><label className="form-label" htmlFor="taste">What do you enjoy playing?</label><textarea id="taste" className="form-textarea" minLength={3} maxLength={500} required value={query} onChange={(e) => setQuery(e.target.value)} placeholder="I like exploration, crafting, co-op, challenging boss fights, and games with a strong story…" /><div className="form-help">Mention genres, mechanics, mood, or gameplay. {query.length}/500 characters.</div></div> : <div className="form-field"><label className="form-label" htmlFor="reference">Choose a reference game</label><select id="reference" className="control" required value={referenceGame} onChange={(e) => setReferenceGame(e.target.value)} disabled={loadingGames}><option value="">{loadingGames ? "Loading games…" : "Choose a game"}</option>{games.map((game) => <option value={game.id} key={game.id}>{game.title}</option>)}</select><div className="form-help">Recommendations use the selected game&apos;s description, genres, and platform metadata.</div></div>}
            {error && <p className="error-text" role="alert" style={{ marginBottom: 14 }}>{error}</p>}
            <button className="button button-primary" disabled={loading || (mode === "description" ? query.trim().length < 3 : !referenceGame)}>{loading ? "Finding your matches…" : "Find similar games ↗"}</button>
          </form>
        </section>
        <aside className="content-panel"><div className="section-kicker">How it works</div><h2 style={{ fontFamily: "Space Grotesk", margin: "8px 0 16px" }}>Meaning, not just keywords.</h2><div className="review-card"><strong>01 · Turn text into vectors</strong><p className="review-body">Game descriptions and your query are converted into numerical embeddings.</p></div><div className="review-card"><strong>02 · Search in PostgreSQL</strong><p className="review-body">pgvector ranks available games by cosine distance against the query vector.</p></div><div className="review-card"><strong>03 · Inspect the matches</strong><p className="review-body">Similarity scores help compare matches. They are not probabilities of enjoyment.</p></div><p className="form-help">The embedding model and retrieval details are described in the project documentation.</p></aside>
      </div>
      {results.length > 0 && <section style={{ marginTop: 38 }}><div className="section-heading"><div><div className="section-kicker">Your results</div><h2>Picks based on {source}</h2><p>Sorted by vector similarity. Open any result to read reviews or save it.</p></div></div><div className="recommend-grid">{results.map((game) => <div key={game.id}><GameCard game={game} /><div style={{ paddingTop: 9 }}><span className="similarity-pill">Vector score · {Number(game.similarity || 0).toFixed(3)}</span></div></div>)}</div></section>}
      {!loading && !error && results.length === 0 && <div className="empty-state" style={{ marginTop: 28 }}><h3>Ready when you are</h3><p>Run a search to see games ranked by vector similarity.</p><Link className="button button-quiet" href="/">Browse all games</Link></div>}
    </>
  );
}
