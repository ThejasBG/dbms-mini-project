-- Apply after: python -m backend.init_db
-- Idempotent migration for the Next.js application and authenticated API.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS email TEXT,
    ADD COLUMN IF NOT EXISTS password_hash TEXT,
    ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'player';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'users_role_allowed_check'
          AND conrelid = 'users'::regclass
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT users_role_allowed_check
            CHECK (role IN ('player', 'admin'));
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS users_email_lower_uq
    ON users (LOWER(email)) WHERE email IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS users_username_lower_uq
    ON users (LOWER(username));

ALTER TABLE games ADD COLUMN IF NOT EXISTS cover_url TEXT;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'games_cover_url_http_check'
          AND conrelid = 'games'::regclass
    ) THEN
        ALTER TABLE games
            ADD CONSTRAINT games_cover_url_http_check
            CHECK (cover_url IS NULL OR cover_url ~* '^https?://');
    END IF;
END $$;

ALTER TABLE reviews
    ADD COLUMN IF NOT EXISTS user_id BIGINT REFERENCES users(id) ON DELETE SET NULL;
CREATE UNIQUE INDEX IF NOT EXISTS reviews_user_game_uq
    ON reviews (user_id, game_id) WHERE user_id IS NOT NULL;

CREATE OR REPLACE VIEW game_review_summary AS
SELECT
    g.id AS game_id,
    g.title,
    COUNT(r.id) FILTER (WHERE r.is_fictional = FALSE) AS genuine_review_count,
    ROUND(
        AVG(r.rating) FILTER (WHERE r.is_fictional = FALSE)::numeric,
        2
    ) AS average_genuine_rating
FROM games AS g
LEFT JOIN reviews AS r ON r.game_id = g.id
GROUP BY g.id, g.title;

CREATE INDEX IF NOT EXISTS games_created_at_idx ON games(created_at DESC);
