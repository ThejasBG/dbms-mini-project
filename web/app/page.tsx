"use client";

import { useEffect, useMemo, useState } from "react";

type Game = {
  id: number;
  title: string;
  description: string;
  genres: string[];
  platforms: string[];
  pricing_model: string;
};

type GamesResponse = {
  items: Game[];
  count: number;
  cached: boolean;
};

type ArtworkEntry = {
  local?: string;
  external?: string;
  source?: string;
};

type ArtworkManifest = Record<string, ArtworkEntry>;

const API_URL = "http://127.0.0.1:8000";

function GameArtwork({
  title,
  index,
  artwork,
}: {
  title: string;
  index: number;
  artwork: ArtworkManifest;
}) {
  const entry = artwork[title];
  const [imageSrc, setImageSrc] = useState(entry?.local || entry?.external || "");
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setImageSrc(entry?.local || entry?.external || "");
    setFailed(false);
  }, [entry?.local, entry?.external]);

  const useFallback = !imageSrc || failed;

  return (
    <div className={`game-art game-art-${index % 6}`}>
      {!useFallback && (
        <img
          className="game-cover"
          src={imageSrc}
          alt={`${title} cover artwork`}
          loading="lazy"
          onError={() => {
            if (
              entry?.local &&
              imageSrc === entry.local &&
              entry.external &&
              entry.external !== entry.local
            ) {
              setImageSrc(entry.external);
            } else {
              setFailed(true);
            }
          }}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "contain",
            objectPosition: "center",
            backgroundColor: "#111318",
            zIndex: 0,
          }}
        />
      )}
      <span className="game-number" style={{ position: "relative", zIndex: 1 }}>
        {String(index + 1).padStart(2, "0")}
      </span>
      {useFallback && (
        <>
          <span className="game-initials">
            {title
              .split(/[\s:]+/)
              .filter(Boolean)
              .slice(0, 2)
              .map((word) => word[0])
              .join("")
              .toUpperCase()}
          </span>
          <span className="game-art-label">STEAMISH DISCOVERY</span>
        </>
      )}
    </div>
  );
}

export default function Home() {
  const [games, setGames] = useState<Game[]>([]);
  const [artwork, setArtwork] = useState<ArtworkManifest>({});
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("/images/games/manifest.json")
      .then((response) => {
        if (!response.ok) throw new Error("Artwork manifest unavailable");
        return response.json();
      })
      .then((data: ArtworkManifest) => setArtwork(data))
      .catch(() => {
        // Keep the CSS artwork fallback if the manifest cannot be loaded.
      });

    async function loadGames() {
      try {
        const response = await fetch(`${API_URL}/api/games`);

        if (!response.ok) {
          throw new Error("Unable to load the game catalogue.");
        }

        const data: GamesResponse = await response.json();
        setGames(data.items);
      } catch {
        setError(
          "Could not connect to Steamish. Make sure the FastAPI backend is running."
        );
      } finally {
        setLoading(false);
      }
    }

    loadGames();
  }, []);

  const filteredGames = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) return games;

    return games.filter((game) =>
      [
        game.title,
        game.description,
        ...game.genres,
        ...game.platforms,
      ]
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
  }, [games, search]);

  return (
    <main className="store">
      <header className="topbar">
        <a className="brand" href="/">
          STEAM<span>ISH</span>
        </a>

        <nav className="navigation">
          <a className="active" href="#home">
            Store
          </a>
          <a href="#catalogue">Discover</a>
          <a href="#catalogue">Browse Games</a>
        </nav>

        <span className="status">
          <span className="status-dot" />
          Catalogue
        </span>
      </header>

      <section className="hero" id="home">
        <div className="hero-content">
          <p className="eyebrow">YOUR NEXT ADVENTURE STARTS HERE</p>
          <h1>
            Find your
            <br />
            next <span>favourite.</span>
          </h1>
          <p className="hero-description">
            Discover worlds worth exploring, challenges worth taking on,
            and games worth playing.
          </p>

          <a className="primary-button" href="#catalogue">
            Explore the catalogue <span aria-hidden="true">→</span>
          </a>

          <div className="hero-stats">
            <div>
              <strong>{games.length || "—"}</strong>
              <span>Games to explore</span>
            </div>
            <div>
              <strong>∞</strong>
              <span>Worlds to discover</span>
            </div>
          </div>
        </div>

        <div className="hero-art" aria-label="Gaming-inspired artwork">
          <div className="art-orbit orbit-one" />
          <div className="art-orbit orbit-two" />
          <div className="art-core">
            <span>PLAY</span>
            <strong>BEYOND</strong>
            <span>THE ORDINARY</span>
          </div>
          <span className="floating-symbol symbol-one">✳</span>
          <span className="floating-symbol symbol-two">✦</span>
          <span className="floating-symbol symbol-three">+</span>
          <div className="art-caption">DISCOVER SOMETHING NEW</div>
        </div>
      </section>

      <section className="catalogue" id="catalogue">
        <div className="section-heading">
          <div>
            <p className="eyebrow">THE COLLECTION</p>
            <h2>Explore games<span>.</span></h2>
          </div>
          <p className="result-count">
            {loading ? "Loading catalogue..." : `${filteredGames.length} games`}
          </p>
        </div>

        <div className="search-row">
          <label className="search-box">
            <span aria-hidden="true">⌕</span>
            <input
              type="search"
              placeholder="Search games, genres or platforms..."
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              aria-label="Search games"
            />
            {search && (
              <button
                type="button"
                className="clear-search"
                onClick={() => setSearch("")}
                aria-label="Clear search"
              >
                ×
              </button>
            )}
          </label>
        </div>

        {loading && (
          <div className="message-panel">
            <div className="loader" />
            <p>Discovering your next favourite...</p>
          </div>
        )}

        {!loading && error && (
          <div className="message-panel error-panel">
            <p>{error}</p>
            <button
              className="secondary-button"
              onClick={() => window.location.reload()}
            >
              Try again
            </button>
          </div>
        )}

        {!loading && !error && filteredGames.length === 0 && (
          <div className="message-panel">
            <p>No games match your search. Try another title or genre.</p>
          </div>
        )}

        {!loading && !error && filteredGames.length > 0 && (
          <div className="game-grid">
            {filteredGames.map((game, index) => (
              <article className="game-card" key={game.id}>
                <GameArtwork
                  title={game.title}
                  index={index}
                  artwork={artwork}
                />

                <div className="game-card-content">
                  <div className="game-card-topline">
                    <span className="game-category">
                      {game.genres[0] || "Game"}
                    </span>
                    <span className="game-price">{game.pricing_model}</span>
                  </div>

                  <h3>{game.title}</h3>
                  <p className="game-description">{game.description}</p>

                  <div className="game-tags">
                    {game.platforms.slice(0, 3).map((platform) => (
                      <span key={platform}>{platform}</span>
                    ))}
                    {game.platforms.length > 3 && (
                      <span>+{game.platforms.length - 3}</span>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <footer className="footer">
        <a className="brand footer-brand" href="#home">
          STEAM<span>ISH</span>
        </a>
        <p>A universe of games. One place to discover them.</p>
        <span>Powered by FastAPI & PostgreSQL</span>
      </footer>
    </main>
  );
}