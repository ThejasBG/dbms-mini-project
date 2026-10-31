-- Run: psql -U postgres -d game_catalog -f sql/tests/constraint_checks.sql
-- Uses a transaction and leaves no persistent test rows.
BEGIN;

DO $$
DECLARE gid BIGINT;
BEGIN
  SELECT id INTO gid FROM games ORDER BY id LIMIT 1;
  IF gid IS NULL THEN RAISE EXCEPTION 'Seed games before running this test'; END IF;
  BEGIN
    INSERT INTO reviews(game_id, username, rating, body)
    VALUES (gid, 'ConstraintCheck', 9, 'This rating is invalid');
    RAISE EXCEPTION 'FAIL: rating CHECK accepted 9';
  EXCEPTION WHEN check_violation THEN
    RAISE NOTICE 'PASS: review rating CHECK rejected 9';
  END;
END $$;

DO $$
DECLARE uid BIGINT; gid BIGINT; n INTEGER;
BEGIN
  SELECT id INTO uid FROM users WHERE username='DemoPlayer';
  SELECT id INTO gid FROM games ORDER BY id LIMIT 1;
  IF uid IS NULL OR gid IS NULL THEN RAISE EXCEPTION 'Seed DemoPlayer and games first'; END IF;
  INSERT INTO wishlist(user_id, game_id) VALUES(uid, gid) ON CONFLICT DO NOTHING;
  INSERT INTO wishlist(user_id, game_id) VALUES(uid, gid) ON CONFLICT DO NOTHING;
  SELECT COUNT(*) INTO n FROM wishlist WHERE user_id=uid AND game_id=gid;
  IF n <> 1 THEN RAISE EXCEPTION 'FAIL: wishlist duplicate protection failed'; END IF;
  RAISE NOTICE 'PASS: wishlist composite primary key prevents duplicates';
END $$;

ROLLBACK;
