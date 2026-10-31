CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS games (
 id BIGSERIAL PRIMARY KEY,
 title TEXT UNIQUE NOT NULL CHECK (char_length(title) BETWEEN 1 AND 200),
 description TEXT NOT NULL,
 genres TEXT[] NOT NULL DEFAULT '{}',
 platforms TEXT[] NOT NULL DEFAULT '{}',
 pricing_model TEXT NOT NULL DEFAULT 'Paid',
 embedding vector(384),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS games_genres_idx ON games USING GIN(genres);
CREATE INDEX IF NOT EXISTS games_platforms_idx ON games USING GIN(platforms);
CREATE INDEX IF NOT EXISTS games_title_lower_idx ON games (lower(title));
CREATE INDEX IF NOT EXISTS games_embedding_hnsw_idx ON games USING hnsw (embedding vector_cosine_ops) WHERE embedding IS NOT NULL;

CREATE TABLE IF NOT EXISTS users (
 id BIGSERIAL PRIMARY KEY,
 username TEXT UNIQUE NOT NULL CHECK (char_length(username) BETWEEN 1 AND 40),
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reviews (
 id BIGSERIAL PRIMARY KEY,
 game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
 username TEXT NOT NULL CHECK (char_length(username) BETWEEN 1 AND 40),
 rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
 body TEXT NOT NULL CHECK (char_length(body) BETWEEN 5 AND 1000),
 is_fictional BOOLEAN NOT NULL DEFAULT FALSE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS reviews_game_created_idx ON reviews(game_id, created_at DESC);
CREATE INDEX IF NOT EXISTS reviews_rating_idx ON reviews(rating);

CREATE TABLE IF NOT EXISTS user_library (
 user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
 added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY(user_id, game_id)
);
CREATE INDEX IF NOT EXISTS user_library_game_idx ON user_library(game_id);

CREATE TABLE IF NOT EXISTS wishlist (
 user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 game_id BIGINT NOT NULL REFERENCES games(id) ON DELETE CASCADE,
 added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 PRIMARY KEY(user_id, game_id)
);
CREATE INDEX IF NOT EXISTS wishlist_game_idx ON wishlist(game_id);

CREATE TABLE IF NOT EXISTS demo_wallets (
 user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
 credits INTEGER NOT NULL DEFAULT 100 CHECK (credits >= 0)
);
