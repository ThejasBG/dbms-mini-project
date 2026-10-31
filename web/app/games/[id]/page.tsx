"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, ApiError, jsonBody } from "@/lib/api";
import type { Game, Review, User } from "@/lib/types";

const palette = ["cover-violet", "cover-blue", "cover-teal", "cover-orange", "cover-pink", "cover-green"];
const icons: Record<string, string> = { RPG: "✦", "Action RPG": "⚔", Adventure: "⌁", Strategy: "♟", Simulation: "⌂", Racing: "↗", Horror: "☾", Indie: "✳", Platformer: "⇧", Shooter: "◎", Survival: "⌖", Sandbox: "◇" };
type GameDetail = Game & { reviews: Review[] };

export default function GameDetailsPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [game, setGame] = useState<GameDetail | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [failure, setFailure] = useState("");
  const [rating, setRating] = useState(5);
  const [body, setBody] = useState("");
  const [posting, setPosting] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true); setError("");
    try { setGame(await api<GameDetail>(`/api/games/${encodeURIComponent(id)}`)); }
    catch (e) { setError(e instanceof ApiError ? e.message : "Could not load this game."); }
    finally { setLoading(false); }
  }, [id]);

  useEffect(() => {
    void Promise.resolve().then(load);
    void api<{ user: User | null }>("/api/auth/me").then((d) => setUser(d.user)).catch(() => setUser(null));
  }, [load]);

  async function saveTo(kind: "wishlist" | "library") {
    setNotice(""); setFailure("");
    try {
      const result = await api<{ message?: string }>(`/api/${kind}/${id}`, { method: "POST" });
      setNotice(result.message || (kind === "wishlist" ? "Saved to your wishlist." : "Added to your library."));
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) setFailure("Sign in first to save games to your personal account.");
      else setFailure(e instanceof Error ? e.message : "Could not save this game.");
    }
  }

  async function submitReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setPosting(true); setNotice(""); setFailure("");
    try {
      await api(`/api/games/${encodeURIComponent(id)}/reviews`, { method: "POST", body: jsonBody({ rating, body }) });
      setBody(""); setNotice("Your review has been saved."); await load();
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) setFailure("Please sign in before publishing a review.");
      else setFailure(e instanceof Error ? e.message : "Could not save the review.");
    } finally { setPosting(false); }
  }

  if (loading) return <div className="loading-state">Loading game profile…</div>;
  if (error || !game) return <div className="error-state"><h3>Game not available</h3><p>{error || "Game not found."}</p><Link href="/" className="button button-primary">Back to discover</Link></div>;
  const color = palette[game.id % palette.length];
  const icon = game.genres?.map((g) => icons[g]).find(Boolean) || "✧";
  const genuineReviews = game.reviews.filter((review) => !review.is_fictional);

  return (
    <>
      <div className="page-heading"><Link href="/" className="inline-link">← Back to catalogue</Link><div className="eyebrow" style={{ marginTop: 20 }}>Game profile</div><h1 className="page-title">{game.title}</h1><div className="tag-row">{game.genres.map((g) => <span className="tag" key={g}>{g}</span>)}</div></div>
      <div className="detail-layout">
        <div>
          <div className={`detail-art ${color}`}>
            {game.cover_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={game.cover_url} alt={`Cover for ${game.title}`} />
            )}
            <span className="detail-symbol" aria-hidden>{icon}</span>
          </div>
          <section style={{ marginTop: 30 }}>
            <div className="section-heading"><div><div className="section-kicker">Player feedback</div><h2>Community reviews</h2><p>{genuineReviews.length} genuine review{genuineReviews.length === 1 ? "" : "s"}. Fictional seed reviews are labelled.</p></div><div className="rating-label" style={{ fontSize: 14 }}><span className="star">★</span> {game.average_rating == null ? "No rating yet" : Number(game.average_rating).toFixed(2)} / 5</div></div>
            <div className="content-panel">
              {game.reviews.length === 0 ? <div className="empty-state"><h3>Be the first to share your take</h3><p>No reviews yet for this game.</p></div> : game.reviews.map((review) => <article className="review-card" key={review.id}>
                <div className="review-head"><strong>{review.username}</strong><span className="rating-label"><span className="star">★</span> {review.rating}/5</span></div>
                <p className="review-body">{review.body}</p><div className="review-meta">{review.is_fictional ? "Fictional demonstration review" : "Community review"} · {new Date(review.created_at).toLocaleDateString()}</div>
              </article>)}
            </div>
          </section>
          <section style={{ marginTop: 25 }} className="content-panel">
            <div className="section-kicker">Your perspective</div><h2 style={{ fontFamily: "Space Grotesk", margin: "8px 0 18px" }}>Write a review</h2>
            {user ? <form onSubmit={submitReview}>
              <div className="form-field"><label className="form-label" htmlFor="rating">Your rating</label><select id="rating" className="control" value={rating} onChange={(e) => setRating(Number(e.target.value))}>{[5,4,3,2,1].map((n) => <option key={n} value={n}>{n} / 5 {n === 5 ? "— Loved it" : n === 1 ? "— Not for me" : "stars"}</option>)}</select></div>
              <div className="form-field"><label className="form-label" htmlFor="review-body">Your review</label><textarea id="review-body" className="form-textarea" minLength={5} maxLength={1000} required value={body} onChange={(e) => setBody(e.target.value)} placeholder="What should another player know? (5–1000 characters)" /><div className="form-help">{body.length}/1000 characters. One review per account and game; posting again updates it.</div></div>
              <button className="button button-primary" type="submit" disabled={posting || body.trim().length < 5}>{posting ? "Publishing…" : "Publish review"}</button>
            </form> : <div><p className="muted" style={{ fontSize: 13 }}>Sign in to post a review associated with your account.</p><Link href="/login" className="button button-primary">Sign in to review</Link></div>}
          </section>
        </div>
        <aside>
          <div className="detail-info-panel"><div className="section-kicker">At a glance</div><div className="meta-line"><span>Pricing</span><span>{game.pricing_model}</span></div><div className="meta-line"><span>Platforms</span><span>{game.platforms.join(", ") || "Not listed"}</span></div><div className="meta-line"><span>Genuine reviews</span><span>{game.review_count ?? genuineReviews.length}</span></div><div className="meta-line"><span>Average rating</span><span>{game.average_rating == null ? "Not rated" : `${Number(game.average_rating).toFixed(2)} / 5`}</span></div>
            <div className="inline-actions" style={{ display: "grid", marginTop: 19 }}><button className="button button-primary" onClick={() => void saveTo("wishlist")}>♡ Add to wishlist</button><button className="button button-quiet" onClick={() => void saveTo("library")}>＋ Add to library</button><Link href={`/recommendations?game_id=${game.id}`} className="button button-outline">Find similar games ↗</Link></div>
            {notice && <p className="success-text" role="status">{notice}</p>}{failure && <p className="error-text" role="alert">{failure} {failure.startsWith("Sign in") && <Link className="inline-link" href="/login">Sign in →</Link>}</p>}
            <p className="form-help" style={{ marginTop: 17 }}>Recommendations use vector similarity between game-description embeddings. Similarity is not a probability that you will enjoy a game.</p>
          </div>
        </aside>
      </div>
    </>
  );
}
