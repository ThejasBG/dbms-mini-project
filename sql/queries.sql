-- Steamish DBMS demonstration queries
-- Run after: python -m backend.init_db

-- 1) DDL: inspect the tables and constraints created by schema.sql.
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' ORDER BY table_name;

-- 2) DML: INSERT + ON CONFLICT (idempotent demo user creation).
INSERT INTO users(username) VALUES ('SQLDemoUser')
ON CONFLICT(username) DO NOTHING;

-- 3) DML: UPDATE inside a transaction; rollback restores the original demo balance.
BEGIN;
UPDATE demo_wallets SET credits=credits+1
WHERE user_id=(SELECT id FROM users WHERE username='DemoPlayer')
RETURNING user_id, credits;
ROLLBACK;

-- 4) JOIN: games with their reviews.
SELECT g.title, r.username, r.rating, r.body
FROM games g INNER JOIN reviews r ON r.game_id=g.id
ORDER BY g.title, r.created_at DESC LIMIT 20;

-- 5) LEFT JOIN: include games even when they have no reviews.
SELECT g.title, COUNT(r.id) AS review_count
FROM games g LEFT JOIN reviews r ON r.game_id=g.id
GROUP BY g.id, g.title ORDER BY review_count DESC, g.title;

-- 6) Aggregation + GROUP BY + HAVING.
SELECT g.title, COUNT(r.id) AS review_count, ROUND(AVG(r.rating)::numeric, 2) AS average_rating
FROM games g JOIN reviews r ON r.game_id=g.id
GROUP BY g.id, g.title HAVING COUNT(r.id) >= 1
ORDER BY average_rating DESC, review_count DESC;

-- 7) GROUP BY genres using unnest.
SELECT genre, COUNT(*) AS games_in_genre
FROM games CROSS JOIN LATERAL unnest(games.genres) AS genre
GROUP BY genre ORDER BY games_in_genre DESC, genre;

-- 8) Subquery: games whose review count is above the catalogue average.
SELECT title FROM games
WHERE id IN (
  SELECT game_id FROM reviews GROUP BY game_id
  HAVING COUNT(*) > (SELECT AVG(review_count)::numeric FROM
    (SELECT COUNT(*) AS review_count FROM reviews GROUP BY game_id) counts)
);

-- 9) Correlated subquery: highest-rated game(s) with at least one review.
SELECT g.title FROM games g
WHERE (SELECT AVG(r.rating) FROM reviews r WHERE r.game_id=g.id) =
      (SELECT MAX(avg_rating) FROM
        (SELECT AVG(rating) AS avg_rating FROM reviews GROUP BY game_id) a);

-- 10) Wishlist DML: insert/remove a sample entry inside a transaction, then undo it.
BEGIN;
INSERT INTO wishlist(user_id, game_id)
SELECT u.id, g.id FROM users u CROSS JOIN games g
WHERE u.username='DemoPlayer' ORDER BY g.id LIMIT 1
ON CONFLICT(user_id,game_id) DO NOTHING;
SELECT u.username, g.title FROM wishlist w
JOIN users u ON u.id=w.user_id JOIN games g ON g.id=w.game_id
WHERE u.username='DemoPlayer';
ROLLBACK;

-- 11) Vector similarity query (pgvector). Replace 384 zeros with a real embedding
-- or use the Python recommendation service, which supplies a generated vector.
-- EXPLAIN (ANALYZE, BUFFERS) SELECT id,title FROM games
-- WHERE embedding IS NOT NULL ORDER BY embedding <=> '[...]'::vector LIMIT 8;

-- 12) Index and query-plan inspection.
SELECT indexname, indexdef FROM pg_indexes
WHERE schemaname='public' ORDER BY tablename, indexname;
EXPLAIN (ANALYZE, BUFFERS)
SELECT id,title FROM games WHERE 'RPG'=ANY(genres) ORDER BY title;

-- 13) DELETE demonstration in a transaction; the rollback preserves the user.
BEGIN;
DELETE FROM users WHERE username='SQLDemoUser';
ROLLBACK;
