"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import GameCard from "@/components/GameCard";
import { api, ApiError } from "@/lib/api";
import type { GameListResponse } from "@/lib/types";

const genres = ["Action", "RPG", "Strategy", "Adventure", "Simulation", "Indie", "Horror", "Roguelike"];
const platforms = ["PC", "PlayStation", "Xbox", "Switch", "Mobile"];

export default function DiscoverPage() {
  const [query, setQuery] = useState("");
  const [genre, setGenre] = useState("");
  const [platform, setPlatform] = useState("");
  const [pricing, setPricing] = useState("");
  const [minRating, setMinRating] = useState("0");
  const [sort, setSort] = useState("popular");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<GameListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setLoading(true);
      setError("");
      const params = new URLSearchParams({ page: String(page), page_size: "12", sort });
      if (query.trim()) params.set("q", query.trim());
      if (genre) params.set("genre", genre);
      if (platform) params.set("platform", platform);
      if (pricing) params.set("pricing_model", pricing);
      if (minRating !== "0") params.set("min_rating", minRating);
      try {
        setData(await api<GameListResponse>(`/api/games?${params.toString()}`, { signal: controller.signal }));
      } catch (e) {
        if (!controller.signal.aborted) {
          setError(e instanceof ApiError ? e.message : "Could not load the catalogue.");
          setData(null);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 200);
    return () => { window.clearTimeout(timer); controller.abort(); };
  }, [query, genre, platform, pricing, minRating, sort, page]);

  function resetFilters() {
    setQuery(""); setGenre(""); setPlatform(""); setPricing(""); setMinRating("0"); setSort("popular"); setPage(1);
  }

  const games = data?.games || [];
  return (
    <>
      <section className="hero">
        <div>
          <div className="eyebrow">Your next favourite is out there</div>
          <h1>Less scrolling.<br /><span>More playing.</span></h1>
          <p>Discover your next obsession with a catalogue built around what you love. Explore by genre, find hidden gems, and let semantic recommendations take you somewhere new.</p>
          <div className="hero-actions">
            <a href="#catalogue" className="button button-primary">Explore the catalogue <span aria-hidden>↓</span></a>
            <Link href="/recommendations" className="button button-outline">Find games for me <span aria-hidden>↗</span></Link>
          </div>
          <div className="stats-strip">
            <div className="stat-card"><div className="stat-value">{data?.total ?? "53+"}</div><div className="stat-label">Matches for current filters</div></div>
            <div className="stat-card"><div className="stat-value">Vector</div><div className="stat-label">Semantic recommendations</div></div>
            <div className="stat-card"><div className="stat-value">Your taste</div><div className="stat-label">Personal library & wishlist</div></div>
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="floating-cover one">✦</div>
          <div className="floating-cover two">⌁</div>
          <div className="floating-cover three">⚔</div>
          <div className="hero-art-caption">Your next world awaits</div>
        </div>
      </section>

      <div className="section-heading">
        <div><div className="section-kicker">Start with a feeling</div><h2>Browse your kind of game</h2></div>
        <span className="text-small">Pick a genre to jump in</span>
      </div>
      <div className="genre-strip">
        {genres.map((item) => <button key={item} className={`genre-chip ${genre === item ? "selected" : ""}`} onClick={() => { setGenre(genre === item ? "" : item); setPage(1); }}>{item}</button>)}
      </div>

      <section id="catalogue">
        <div className="section-heading">
          <div><div className="section-kicker">The collection</div><h2>Find your next favourite</h2><p>Search the catalogue or narrow it down with filters.</p></div>
          <Link href="/recommendations" className="inline-link">Try smart recommendations ↗</Link>
        </div>
        <div className="search-panel">
          <div className="search-field"><span className="search-icon" aria-hidden>⌕</span><input className="search-input" aria-label="Search games" placeholder="Search games, descriptions, genres…" value={query} onChange={(e) => { setQuery(e.target.value); setPage(1); }} /></div>
          <select className="control" aria-label="Filter by genre" value={genre} onChange={(e) => { setGenre(e.target.value); setPage(1); }}><option value="">All genres</option>{genres.concat(["FPS", "Sandbox", "Survival", "Co-op", "Racing", "Puzzle", "Deckbuilder", "Battle Royale", "MMORPG", "Metroidvania", "Sports", "Automation"]).filter((v, i, a) => a.indexOf(v) === i).sort().map((v) => <option key={v}>{v}</option>)}</select>
          <select className="control" aria-label="Filter by platform" value={platform} onChange={(e) => { setPlatform(e.target.value); setPage(1); }}><option value="">All platforms</option>{platforms.map((v) => <option key={v}>{v}</option>)}</select>
          <select className="control" aria-label="Filter by pricing" value={pricing} onChange={(e) => { setPricing(e.target.value); setPage(1); }}><option value="">Any pricing</option><option>Free-to-play</option><option>Paid</option><option>Subscription</option></select>
          <select className="control" aria-label="Minimum rating" value={minRating} onChange={(e) => { setMinRating(e.target.value); setPage(1); }}><option value="0">Any rating</option><option value="3">3.0+ rating</option><option value="4">4.0+ rating</option><option value="4.5">4.5+ rating</option></select>
        </div>
        <div className="results-row">
          <span>{loading ? "Searching catalogue…" : <><strong>{data?.total ?? 0}</strong> games match your filters</>}</span>
          <div style={{ display: "flex", alignItems: "center", gap: 9 }}><label htmlFor="sort" className="text-small">Sort by</label><select id="sort" className="control" value={sort} style={{ width: 170, height: 36 }} onChange={(e) => { setSort(e.target.value); setPage(1); }}><option value="popular">Most reviewed</option><option value="rating">Highest rated</option><option value="newest">Recently added</option><option value="title_asc">Title A–Z</option><option value="title_desc">Title Z–A</option></select><button className="button button-quiet button-small" onClick={resetFilters}>Reset</button></div>
        </div>
        {error && <div className="error-state"><h3>Couldn’t load the catalogue</h3><p>{error}</p><p className="text-small">Check that PostgreSQL and the Python HTTP API are running.</p><button className="button button-quiet" onClick={() => window.location.reload()}>Try again</button></div>}
        {!error && loading && <div className="game-grid">{Array.from({ length: 8 }).map((_, i) => <div className="skeleton" key={i} />)}</div>}
        {!error && !loading && games.length === 0 && <div className="empty-state"><h3>No games found</h3><p>Try another search or remove one of the filters.</p><button className="button button-quiet" onClick={resetFilters}>Clear filters</button></div>}
        {!error && !loading && games.length > 0 && <div className="game-grid">{games.map((game) => <GameCard game={game} key={game.id} />)}</div>}
        {!error && (data?.pages || 0) > 1 && <div className="pagination"><button disabled={page <= 1 || loading} onClick={() => setPage((p) => Math.max(1, p - 1))}>←</button>{Array.from({ length: data?.pages || 1 }, (_, i) => i + 1).filter((p) => p === 1 || p === data?.pages || Math.abs(p - page) <= 1).map((p, idx, arr) => <span key={p} style={{ display: "contents" }}>{idx > 0 && p - arr[idx - 1] > 1 && <span className="muted">…</span>}<button className={p === page ? "current" : ""} aria-current={p === page ? "page" : undefined} onClick={() => setPage(p)}>{p}</button></span>)}<button disabled={page >= (data?.pages || 1) || loading} onClick={() => setPage((p) => p + 1)}>→</button></div>}
      </section>
    </>
  );
}
