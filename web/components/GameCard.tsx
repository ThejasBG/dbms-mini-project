"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { Game } from "@/lib/types";

type ArtworkEntry = { local?: string; external?: string };
type ArtworkManifest = Record<string, ArtworkEntry>;

let artworkManifestPromise: Promise<ArtworkManifest> | null = null;

function loadArtworkManifest(): Promise<ArtworkManifest> {
  if (!artworkManifestPromise) {
    artworkManifestPromise = fetch("/images/games/manifest.json")
      .then((response) => {
        if (!response.ok) throw new Error("Artwork manifest unavailable");
        return response.json() as Promise<ArtworkManifest>;
      })
      .catch(() => ({}));
  }
  return artworkManifestPromise;
}

const genreIcons: Record<string, string> = {
  RPG: "✦", "Action RPG": "⚔", Adventure: "⌁", Strategy: "♟", Simulation: "⌂",
  Racing: "↗", Horror: "☾", Indie: "✳", Platformer: "⇧", Shooter: "◎", FPS: "◎",
  Survival: "⌖", Sandbox: "◇", Cozy: "☼", Roguelike: "⤨", Puzzle: "▦",
};
const palettes = ["cover-violet", "cover-blue", "cover-teal", "cover-orange", "cover-pink", "cover-green"];

export default function GameCard({ game, compact = false }: { game: Game; compact?: boolean }) {
  const [artworkState, setArtworkState] = useState<{ title: string; entry: ArtworkEntry | null }>({ title: "", entry: null });
  const [failedImages, setFailedImages] = useState<{ key: string; sources: string[] }>({ key: "", sources: [] });
  const palette = palettes[Math.abs(Number(game.id) || 0) % palettes.length];
  const rating = game.average_rating == null ? null : Number(game.average_rating);
  const icon = game.genres?.map((g) => genreIcons[g]).find(Boolean) || "✧";
  useEffect(() => {
    let active = true;
    void loadArtworkManifest().then((manifest) => {
      if (active) setArtworkState({ title: game.title, entry: manifest[game.title] || null });
    });
    return () => { active = false; };
  }, [game.title]);

  const artwork = artworkState.title === game.title ? artworkState.entry : null;
  const imageCandidates = [...new Set([game.cover_url, artwork?.local, artwork?.external].filter((value): value is string => Boolean(value)))];
  const imageKey = `${game.id}:${imageCandidates.join("|")}`;
  const failedForGame = failedImages.key === imageKey ? failedImages.sources : [];
  const imageSrc = imageCandidates.find((candidate) => !failedForGame.includes(candidate));

  return (
    <article className={`game-card ${compact ? "game-card-compact" : ""}`}>
      <Link href={`/games/${game.id}`} className={`game-art ${palette}`} aria-label={`View ${game.title}`}>
        {imageSrc ? (
          // Optional catalogue artwork. The CSS art remains visible when no cover is available.
          // eslint-disable-next-line @next/next/no-img-element
          <img className="game-art-image" src={imageSrc} alt="" loading="lazy" onError={() => setFailedImages({ key: imageKey, sources: [...failedForGame, imageSrc] })} />
        ) : <span className="art-symbol" aria-hidden>{icon}</span>}
        <span className="art-shine" />
        <span className="art-platforms">{(game.platforms || []).slice(0, 3).join(" · ")}</span>
      </Link>
      <div className="game-card-info">
        <div className="game-card-heading">
          <Link href={`/games/${game.id}`} className="game-title">{game.title}</Link>
          <span className={`price-badge ${game.pricing_model === "Free-to-play" ? "free" : ""}`}>
            {game.pricing_model === "Free-to-play" ? "Free" : game.pricing_model === "Subscription" ? "Sub" : "Paid"}
          </span>
        </div>
        <p className="game-description">{game.description}</p>
        <div className="game-card-footer">
          <div className="tag-row">{(game.genres || []).slice(0, 2).map((genre) => <span className="tag" key={genre}>{genre}</span>)}</div>
          <div className="rating-label" title={rating == null ? "No genuine ratings yet" : `${rating.toFixed(1)} out of 5`}>
            <span className="star">★</span> {rating == null ? "New" : rating.toFixed(1)}
            {typeof game.review_count === "number" && <span className="rating-count">({game.review_count})</span>}
          </div>
        </div>
      </div>
    </article>
  );
}
