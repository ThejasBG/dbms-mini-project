"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";

type CountRow = { name: string; count: number };
type RatedRow = { id: number; title: string; average_rating: number | string; review_count: number };
type Analytics = {
  overview: { total_games: number; genuine_reviews: number; registered_users: number; wishlist_entries: number };
  genres: CountRow[]; platforms: CountRow[]; top_rated: RatedRow[]; most_reviewed: { id: number; title: string; review_count: number }[];
};

function Bars({ rows, empty }: { rows: CountRow[]; empty: string }) {
  const max = Math.max(...rows.map((r) => Number(r.count)), 1);
  if (!rows.length) return <p className="muted" style={{ fontSize: 12 }}>{empty}</p>;
  return <div className="bar-list">{rows.map((row) => <div className="bar-row" key={row.name}><span className="bar-label" title={row.name}>{row.name}</span><div className="bar-track"><div className="bar-fill" style={{ width: `${Math.max(3, Number(row.count) / max * 100)}%` }} /></div><span className="bar-count">{row.count}</span></div>)}</div>;
}

export default function AnalyticsPage() {
  const [data, setData] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    api<Analytics>("/api/analytics").then(setData).catch((e) => setError(e instanceof ApiError ? e.message : "Could not load the analytics." )).finally(() => setLoading(false));
  }, []);

  return <>
    <div className="page-heading"><div className="eyebrow">SQL-powered insights</div><h1 className="page-title">The catalogue, in context.</h1><p>Every figure below is calculated from PostgreSQL data at request time. Fictional seed reviews are excluded from genuine-review summaries.</p></div>
    {loading && <div className="loading-state">Calculating catalogue insights…</div>}
    {!loading && error && <div className="error-state"><h3>Analytics unavailable</h3><p>{error}</p><p className="text-small">Check that the database and API are running, and that the application migration has been applied.</p></div>}
    {!loading && data && <>
      <div className="stats-strip" style={{ gridTemplateColumns: "repeat(4, minmax(0,1fr))" }}>
        <div className="stat-card"><div className="stat-value">{data.overview.total_games.toLocaleString()}</div><div className="stat-label">Games in catalogue</div></div>
        <div className="stat-card"><div className="stat-value">{data.overview.genuine_reviews.toLocaleString()}</div><div className="stat-label">Genuine reviews</div></div>
        <div className="stat-card"><div className="stat-value">{data.overview.registered_users.toLocaleString()}</div><div className="stat-label">Registered accounts</div></div>
        <div className="stat-card"><div className="stat-value">{data.overview.wishlist_entries.toLocaleString()}</div><div className="stat-label">Wishlist entries</div></div>
      </div>
      <div className="two-column">
        <section className="content-panel"><div className="section-kicker">Catalogue mix</div><h2 style={{ fontFamily: "Space Grotesk", margin: "7px 0 22px" }}>Games by genre</h2><Bars rows={data.genres} empty="No genre data is available." /></section>
        <section className="content-panel"><div className="section-kicker">Where people play</div><h2 style={{ fontFamily: "Space Grotesk", margin: "7px 0 22px" }}>Platform coverage</h2><Bars rows={data.platforms} empty="No platform data is available." /></section>
      </div>
      <div className="two-column" style={{ marginTop: 22 }}>
        <section className="content-panel"><div className="section-kicker">Minimum two genuine reviews</div><h2 style={{ fontFamily: "Space Grotesk", margin: "7px 0 18px" }}>Highest-rated games</h2>{data.top_rated.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Game</th><th>Rating</th><th>Reviews</th></tr></thead><tbody>{data.top_rated.map((g) => <tr key={g.id}><td><Link className="inline-link" href={`/games/${g.id}`}>{g.title}</Link></td><td><span className="star">★</span> {Number(g.average_rating).toFixed(2)}</td><td>{g.review_count}</td></tr>)}</tbody></table></div> : <p className="muted">Not enough genuine reviews yet.</p>}</section>
        <section className="content-panel"><div className="section-kicker">Community activity</div><h2 style={{ fontFamily: "Space Grotesk", margin: "7px 0 18px" }}>Most reviewed games</h2>{data.most_reviewed.length ? <div className="table-wrap"><table className="data-table"><thead><tr><th>Game</th><th>Genuine reviews</th></tr></thead><tbody>{data.most_reviewed.map((g) => <tr key={g.id}><td><Link className="inline-link" href={`/games/${g.id}`}>{g.title}</Link></td><td>{g.review_count}</td></tr>)}</tbody></table></div> : <p className="muted">Genuine reviews will appear here as players contribute.</p>}</section>
      </div>
      <p className="form-help" style={{ marginTop: 20 }}>DBMS examples used: JOIN, GROUP BY, HAVING, COUNT, AVG, filtered aggregates, UNNEST, ORDER BY, and a review-summary view for game profiles.</p>
    </>}
  </>;
}
