"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import GameCard from "@/components/GameCard";
import { api, ApiError } from "@/lib/api";
import type { Game } from "@/lib/types";

export default function CollectionView({ kind }: { kind: "wishlist" | "library" }) {
  const [games, setGames] = useState<Game[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { const result = await api<{ games: Game[] }>(`/api/${kind}`); setGames(result.games); }
    catch (e) { setError(e instanceof ApiError ? e.message : "Could not load your collection."); }
    finally { setLoading(false); }
  }, [kind]);
  useEffect(() => { void Promise.resolve().then(load); }, [load]);

  async function remove(gameId: number) {
    setNotice("");
    try {
      await api(`/api/${kind}/${gameId}`, { method: "DELETE" });
      setNotice("Game removed from your collection.");
      await load();
    } catch (e) { setError(e instanceof Error ? e.message : "Could not remove the game."); }
  }

  const wishlist = kind === "wishlist";
  return (
    <>
      <div className="page-heading"><div className="eyebrow">Your space</div><h1 className="page-title">{wishlist ? "The wishlist." : "Your library."}</h1><p>{wishlist ? "Keep track of the games on your radar. Your list is stored in PostgreSQL and tied to your account." : "Your personal collection, all in one place. Add a game from its detail page to keep it close."}</p></div>
      {notice && <p className="success-text" role="status">{notice}</p>}
      {loading && <div className="loading-state">Loading your {kind}…</div>}
      {!loading && error && <div className="empty-state"><h3>{error.includes("Sign in") ? "Your account, your collection" : "Couldn't load this page"}</h3><p>{error}</p>{error.includes("Sign in") ? <Link className="button button-primary" href="/login">Sign in</Link> : <button className="button button-quiet" onClick={() => void load()}>Try again</button>}</div>}
      {!loading && !error && games.length === 0 && <div className="empty-state"><h3>{wishlist ? "Your wishlist is waiting" : "A library with room to grow"}</h3><p>{wishlist ? "Save games you want to play later using the heart button on a game page." : "Browse the catalogue and add games to your library."}</p><Link className="button button-primary" href="/">Explore games ↗</Link></div>}
      {!loading && !error && games.length > 0 && <><div className="results-row"><span><strong>{games.length}</strong> saved game{games.length === 1 ? "" : "s"}</span><Link href="/" className="inline-link">Discover more ↗</Link></div><div className="game-grid">{games.map((game) => <div key={game.id}><GameCard game={game} />{wishlist && <button className="button button-danger button-block" style={{ marginTop: 8 }} onClick={() => void remove(game.id)}>Remove from wishlist</button>}{!wishlist && <button className="button button-quiet button-block" style={{ marginTop: 8 }} onClick={() => void remove(game.id)}>Remove from library</button>}</div>)}</div></>}
    </>
  );
}
