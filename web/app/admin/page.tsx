"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError, jsonBody } from "@/lib/api";
import type { Game, GameListResponse, User } from "@/lib/types";

type FormState = { title: string; description: string; genres: string; platforms: string; pricing_model: string; cover_url: string };
const blank: FormState = { title: "", description: "", genres: "", platforms: "", pricing_model: "Paid", cover_url: "" };

export default function AdminPage() {
  const [user, setUser] = useState<User | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [games, setGames] = useState<Game[]>([]);
  const [form, setForm] = useState<FormState>(blank);
  const [editId, setEditId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadGames = useCallback(async () => {
    const first = await api<GameListResponse>("/api/games?page=1&page_size=48&sort=title_asc");
    let all = first.games;
    if (first.pages > 1) {
      const rest = await Promise.all(Array.from({ length: first.pages - 1 }, (_, i) => api<GameListResponse>(`/api/games?page=${i + 2}&page_size=48&sort=title_asc`)));
      all = all.concat(...rest.map((r) => r.games));
    }
    setGames(all);
  }, []);

  useEffect(() => {
    api<{ user: User | null }>("/api/auth/me").then((d) => setUser(d.user)).catch(() => setUser(null)).finally(() => setAuthChecked(true));
  }, []);
  useEffect(() => {
    if (user?.role !== "admin") return;
    let active = true;
    void Promise.resolve().then(loadGames).catch((e) => {
      if (active) setError(e instanceof Error ? e.message : "Could not load the catalogue.");
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [user, loadGames]);

  function beginEdit(game: Game) {
    setEditId(game.id);
    setForm({ title: game.title, description: game.description, genres: game.genres.join(", "), platforms: game.platforms.join(", "), pricing_model: game.pricing_model, cover_url: game.cover_url || "" });
    setError(""); setNotice(""); window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function cancelEdit() { setEditId(null); setForm(blank); setError(""); setNotice(""); }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    const payload = { title: form.title, description: form.description, genres: form.genres.split(",").map((s) => s.trim()).filter(Boolean), platforms: form.platforms.split(",").map((s) => s.trim()).filter(Boolean), pricing_model: form.pricing_model, cover_url: form.cover_url.trim() || null };
    try {
      await api(editId ? `/api/admin/games/${editId}` : "/api/admin/games", { method: editId ? "PUT" : "POST", body: jsonBody(payload) });
      setNotice(editId ? "Game details updated and its embedding regenerated." : "Game added and its embedding generated.");
      setEditId(null); setForm(blank); await loadGames();
    } catch (e) { setError(e instanceof ApiError ? e.message : "Could not save the game."); }
    finally { setBusy(false); }
  }

  async function deleteGame(game: Game) {
    if (!window.confirm(`Delete “${game.title}”? Related reviews, library entries, and wishlist entries will also be removed by foreign-key rules.`)) return;
    setError(""); setNotice("");
    try { await api(`/api/admin/games/${game.id}`, { method: "DELETE" }); setNotice(`${game.title} was removed.`); if (editId === game.id) cancelEdit(); await loadGames(); }
    catch (e) { setError(e instanceof Error ? e.message : "Could not delete the game."); }
  }

  if (!authChecked) return <div className="loading-state">Checking access…</div>;
  if (!user) return <div className="empty-state"><h3>Administrator sign-in required</h3><p>Sign in with an account that has the administrator role to manage the catalogue.</p><Link href="/login" className="button button-primary">Sign in</Link></div>;
  if (user.role !== "admin") return <div className="empty-state"><h3>Admin access required</h3><p>This account has the player role. To promote a trusted project administrator, follow the one-time SQL command in the application setup guide.</p><Link href="/" className="button button-quiet">Back to discover</Link></div>;

  return <>
    <div className="page-heading"><div className="eyebrow">Catalogue control</div><h1 className="page-title">Admin workspace.</h1><p>Add, edit, or remove catalogue entries. Each save generates an embedding so semantic recommendations stay aligned with the game metadata.</p></div>
    <div className="two-column" style={{ alignItems: "start" }}>
      <section className="content-panel">
        <div className="section-kicker">{editId ? `Editing game #${editId}` : "New catalogue entry"}</div><h2 style={{ fontFamily: "Space Grotesk", margin: "7px 0 20px" }}>{editId ? "Update game" : "Add a game"}</h2>
        <form onSubmit={submit}>
          <div className="form-field"><label className="form-label" htmlFor="title">Game title</label><input id="title" className="form-input" required maxLength={140} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></div>
          <div className="form-field"><label className="form-label" htmlFor="description">Description</label><textarea id="description" className="form-textarea" required minLength={10} maxLength={4000} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /><div className="form-help">Metadata text is used to generate the game&apos;s 384-dimensional embedding.</div></div>
          <div className="form-field"><label className="form-label" htmlFor="genres">Genres (comma-separated)</label><input id="genres" className="form-input" required value={form.genres} onChange={(e) => setForm({ ...form, genres: e.target.value })} placeholder="RPG, Open World" /></div>
          <div className="form-field"><label className="form-label" htmlFor="platforms">Platforms (comma-separated)</label><input id="platforms" className="form-input" required value={form.platforms} onChange={(e) => setForm({ ...form, platforms: e.target.value })} placeholder="PC, PlayStation, Xbox" /></div>
          <div className="form-grid"><div className="form-field"><label className="form-label" htmlFor="pricing">Pricing model</label><select id="pricing" className="control" value={form.pricing_model} onChange={(e) => setForm({ ...form, pricing_model: e.target.value })}><option>Paid</option><option>Free-to-play</option><option>Subscription</option></select></div><div className="form-field"><label className="form-label" htmlFor="cover">Cover image URL (optional)</label><input id="cover" className="form-input" type="url" value={form.cover_url} onChange={(e) => setForm({ ...form, cover_url: e.target.value })} placeholder="https://…" /></div></div>
          {error && <p className="error-text" role="alert" style={{ marginBottom: 13 }}>{error}</p>}{notice && <p className="success-text" role="status" style={{ marginBottom: 13 }}>{notice}</p>}
          <div className="inline-actions"><button type="submit" className="button button-primary" disabled={busy}>{busy ? "Saving…" : editId ? "Save changes" : "Add game"}</button>{editId && <button type="button" className="button button-quiet" onClick={cancelEdit}>Cancel edit</button>}</div>
        </form>
      </section>
       <section className="content-panel"><div className="section-kicker">Current data</div><h2 style={{ fontFamily: "Space Grotesk", margin: "7px 0 18px" }}>Catalogue ({games.length})</h2>
         {loading ? <p className="muted">Loading games…</p> : <div className="table-wrap"><table className="data-table"><thead><tr><th>Game</th><th>Genre</th><th>Actions</th></tr></thead><tbody>{games.map((game) => <tr key={game.id}><td><Link className="inline-link" href={`/games/${game.id}`}>{game.title}</Link><div className="form-help">#{game.id}</div></td><td>{game.genres.slice(0, 2).join(", ")}</td><td><div className="table-actions"><button className="button button-quiet button-small" onClick={() => beginEdit(game)}>Edit</button><button className="button button-danger button-small" onClick={() => void deleteGame(game)}>Delete</button></div></td></tr>)}</tbody></table></div>}
      </section>
    </div>
  </>;
}
