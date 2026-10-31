# Advanced database concepts implemented

1. **Transactions and ACID consistency** — `backend/db.py` wraps multi-statement writes in `connection.transaction()`. `backend/service.py::transfer` debits and credits wallets in one transaction. An exception aborts both writes.
2. **Concurrency control / pessimistic row locking** — `transfer` locks the two user rows and wallet rows with `SELECT ... FOR UPDATE`, always in a stable ID order to reduce deadlock risk.
3. **Referential integrity and cascading actions** — foreign keys connect reviews, library, wishlist, and wallets to their parent rows with `ON DELETE CASCADE`.
4. **Declarative integrity constraints** — primary keys, unique constraints, CHECK constraints for review ratings/body and non-negative wallet credits, plus composite keys preventing duplicate library/wishlist entries.
5. **Indexing and query planning** — GIN indexes support array membership for genres/platforms; B-tree indexes support title/review/library/wishlist lookups; HNSW cosine index accelerates pgvector nearest-neighbour searches. Use `sql/queries.sql` and `EXPLAIN (ANALYZE, BUFFERS)` to inspect plans.
6. **Vector similarity search** — 384-dimensional Sentence Transformer embeddings are stored in pgvector and compared using cosine distance (`<=>`).
7. **Caching** — optional Redis caches catalogue reads; PostgreSQL remains the source of truth.

## Reproducible verification

Run `python -m backend.test_db` after `python -m backend.init_db`. It checks table presence, pgvector and embedding dimensions, wishlist uniqueness, review CHECK constraints, foreign keys, and a forced transaction rollback. Run `psql -d game_catalog -f sql/verify_schema.sql` and `psql -d game_catalog -f sql/queries.sql` for structural and SQL demonstrations.

The project does not claim production-grade authentication or reviewer accounts: review `username` is a display name. The database integrity guarantees described here apply to the stored rows and operations in this learning project.
