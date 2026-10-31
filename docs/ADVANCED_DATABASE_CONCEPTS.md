# Advanced database concepts implemented

This note covers the database concepts used by the existing Streamlit implementation and the Next.js application. Verify `sql/schema.sql` and `sql/migrations/001_application_features.sql` before reporting the final schema.

1. **Transactions and ACID consistency** — `backend/db.py` wraps multi-statement writes in `connection.transaction()`. The legacy demo-credit transfer debits and credits wallets in one transaction. An exception aborts both writes.
2. **Concurrency control / pessimistic row locking** — the legacy `transfer` service locks user and wallet rows with `SELECT ... FOR UPDATE` in a stable ID order to reduce deadlock risk.
3. **Referential integrity** — foreign keys connect reviews, library entries, wishlist entries and demo wallets to their parent rows; delete rules preserve the intended integrity behaviour.
4. **Declarative integrity constraints** — primary keys, unique constraints, CHECK constraints for review ratings/body and non-negative wallet balances, plus composite keys preventing duplicate library/wishlist entries.
5. **Indexing and query planning** — GIN indexes support array membership for genres/platforms; B-tree indexes support selected catalogue/review/library/wishlist lookups; the existing vector index can accelerate pgvector searches. Use `EXPLAIN (ANALYZE, BUFFERS)` to inspect actual plans.
6. **Vector similarity search** — 384-dimensional Sentence Transformer embeddings are stored in pgvector and compared using cosine distance (`<=>`). The API returns a similarity score, not a probability of user satisfaction.
7. **Views and filtered aggregates** — `game_review_summary` calculates counts and average ratings while excluding fictional seed reviews from genuine-review statistics.
8. **SQL analytics** — analytics endpoints use `UNNEST`, joins, filtered aggregates, `GROUP BY`, `HAVING`, `ORDER BY`, and `COUNT`/`AVG` calculations against real database records.
9. **Account-specific relationships** — the wishlist and library use composite primary keys. New authenticated reviews reference a user record, with a partial unique index enforcing one review per user/game.
10. **Caching** — optional Redis caches catalogue reads in the Streamlit prototype. PostgreSQL remains the source of truth.

## Verification commands

Run `python -m backend.init_db`, apply `sql/migrations/001_application_features.sql`, and then run `python -m backend.test_db` plus `python -m backend.test_http_api`. The HTTP API requires PostgreSQL/pgvector for feature integration, while the auth-helper tests do not issue database queries. Run `psql -d game_catalog -f sql/verify_schema.sql` and `psql -d game_catalog -f sql/queries.sql` for structural and SQL demonstrations.

The project remains an academic learning system. Email verification, password recovery, rate limiting, review moderation workflow, production deployment hardening, monitoring, and backups are not implemented by this application upgrade.
