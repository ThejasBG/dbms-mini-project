-- Structural verification for the Steamish schema.
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema='public'
  AND table_name IN ('games','users','reviews','user_library','wishlist','demo_wallets')
ORDER BY table_name, ordinal_position;

SELECT tc.table_name, tc.constraint_name, tc.constraint_type
FROM information_schema.table_constraints tc
WHERE tc.table_schema='public'
  AND tc.table_name IN ('games','users','reviews','user_library','wishlist','demo_wallets')
ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name;

SELECT conrelid::regclass AS table_name, conname, pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE connamespace='public'::regnamespace
ORDER BY conrelid::regclass::text, conname;

SELECT tablename, indexname, indexdef
FROM pg_indexes WHERE schemaname='public'
ORDER BY tablename, indexname;

SELECT COUNT(*) AS games,
       COUNT(*) FILTER (WHERE embedding IS NOT NULL) AS embedded_games
FROM games;
