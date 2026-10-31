"""Integration checks for schema integrity and transaction rollback.

Run after initialization and while PostgreSQL is available:
    python -m backend.test_db
The script uses temporary test records and rolls them back; it does not alter
DemoPlayer/DemoFriend balances or keep test wishlist/review records.
"""
from backend.db import connect


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    c = connect()
    try:
        required = {"games", "users", "reviews", "user_library", "wishlist", "demo_wallets"}
        found = {r["table_name"] for r in c.execute("""SELECT table_name FROM information_schema.tables
                    WHERE table_schema='public' AND table_type='BASE TABLE'""").fetchall()}
        assert_true(required.issubset(found), f"Missing tables: {sorted(required-found)}")

        ext = c.execute("SELECT extversion FROM pg_extension WHERE extname='vector'").fetchone()
        assert_true(ext is not None, "pgvector extension is not installed in this database")
        dims = c.execute("SELECT vector_dims(embedding) AS dims FROM games WHERE embedding IS NOT NULL LIMIT 1").fetchone()
        assert_true(dims and dims["dims"] == 384, "Expected 384-dimensional game embeddings")

        game = c.execute("SELECT id FROM games ORDER BY id LIMIT 1").fetchone()
        user = c.execute("SELECT id FROM users WHERE username='DemoPlayer'").fetchone()
        assert_true(game and user, "Seed a game and DemoPlayer before running tests")

        # Confirm composite PK makes duplicate wishlist rows impossible.
        with c.transaction():
            c.execute("INSERT INTO wishlist(user_id,game_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (user["id"], game["id"]))
            c.execute("INSERT INTO wishlist(user_id,game_id) VALUES (%s,%s) ON CONFLICT DO NOTHING", (user["id"], game["id"]))
            n = c.execute("SELECT COUNT(*) AS n FROM wishlist WHERE user_id=%s AND game_id=%s", (user["id"], game["id"])).fetchone()["n"]
            assert_true(n == 1, "Wishlist composite key did not prevent duplicate rows")
            c.execute("DELETE FROM wishlist WHERE user_id=%s AND game_id=%s", (user["id"], game["id"]))

        # CHECK constraints must reject invalid ratings and wallet balances.
        invalid_rating_rejected = False
        try:
            with c.transaction():
                c.execute("INSERT INTO reviews(game_id,username,rating,body) VALUES (%s,'ConstraintTest',6,'invalid rating')", (game["id"],))
        except Exception:
            invalid_rating_rejected = True
        assert_true(invalid_rating_rejected, "Review rating CHECK constraint did not reject 6")

        # Verify transaction rollback: make a temporary wallet change, force an
        # exception, and confirm the committed balance remains unchanged.
        before = c.execute("SELECT credits FROM demo_wallets WHERE user_id=%s", (user["id"],)).fetchone()
        assert_true(before is not None, "DemoPlayer wallet missing")
        rollback_seen = False
        try:
            with c.transaction():
                c.execute("UPDATE demo_wallets SET credits=credits+17 WHERE user_id=%s", (user["id"],))
                raise RuntimeError("intentional rollback test")
        except RuntimeError:
            rollback_seen = True
        after = c.execute("SELECT credits FROM demo_wallets WHERE user_id=%s", (user["id"],)).fetchone()
        assert_true(rollback_seen and after["credits"] == before["credits"], "Transaction rollback failed")

        fk_count = c.execute("""SELECT COUNT(*) AS n FROM pg_constraint
                              WHERE contype='f' AND connamespace='public'::regnamespace
                                AND conrelid IN ('reviews'::regclass,'user_library'::regclass,
                                                 'wishlist'::regclass,'demo_wallets'::regclass)""").fetchone()["n"]
        assert_true(fk_count >= 6, f"Expected at least 6 foreign keys; found {fk_count}")
        print("PASS: required tables, pgvector/384D embeddings, wishlist uniqueness, review CHECK, foreign keys, and transaction rollback.")
    finally:
        c.close()


if __name__ == "__main__":
    main()
