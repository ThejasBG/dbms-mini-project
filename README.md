# Steamish — Game Discovery and Database Systems Project

A Steam-inspired catalogue and content-based game recommender. It stores game metadata and reviews, not game files. PostgreSQL is the source of truth; pgvector stores 384-dimensional embeddings; Redis is optional.

## Run on Windows without Docker

1. Install PostgreSQL 18 and a compatible pgvector build. Create `game_catalog`, connect to it, and run `CREATE EXTENSION IF NOT EXISTS vector;`.
2. Copy `.env.example` to `.env` and set `DATABASE_URL` to your local PostgreSQL credentials. Never commit `.env`.
3. Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. Initialize/upgrade the schema and seed the catalogue:

```powershell
python -m backend.init_db
```

This is safe to rerun: tables and indexes are created idempotently, games are upserted, and sample reviews are seeded only when needed.

5. Start the backend in Terminal 1:

```powershell
python -m backend.server
```

6. Start the frontend in Terminal 2:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

## Database requirements and evidence

| Requirement | Implementation / evidence |
|---|---|
| PostgreSQL schema | `sql/schema.sql` |
| pgvector + embeddings | `backend/init_db.py`, `backend/embeddings.py`; verify with `python -m backend.test_db` |
| ER diagram | `docs/ER_DIAGRAM.md` (Mermaid) |
| PK/FK/CHECK/UNIQUE/indexes | `sql/schema.sql`; inspect with `sql/verify_schema.sql` |
| DDL and DML | `sql/schema.sql`, `sql/queries.sql` |
| Joins, aggregation, grouping, subqueries | `sql/queries.sql` sections 4–9 |
| Advanced database concepts | `docs/ADVANCED_DATABASE_CONCEPTS.md` |
| Transaction consistency and rollback | `backend/service.py::transfer`; forced rollback test in `backend/test_db.py` |
| Wishlist and review constraints | `wishlist` table and service actions; review CHECK constraints; `backend/test_db.py` |
| Important SQL queries | `sql/queries.sql`, `sql/verify_schema.sql` |

Run the SQL demonstrations in psql:

```powershell
psql -U postgres -d game_catalog -f sql/verify_schema.sql
psql -U postgres -d game_catalog -f sql/queries.sql
```

Run the automated database checks:

```powershell
python -m backend.test_db
```

## Features

- Search/filter a seeded 53-game catalogue.
- Game details and community review submission (seed reviews are explicitly fictional).
- Content-based recommendations using pgvector cosine similarity.
- Add games to a personal demo library and wishlist; remove wishlist items.
- Atomic demo-credit transfers with row locking and rollback safety.
- Optional Redis catalogue caching.

## ER diagram and advanced concepts

See `docs/ER_DIAGRAM.md` and `docs/ADVANCED_DATABASE_CONCEPTS.md`. The diagram is intended to match the implemented schema in `sql/schema.sql`.

## Notes and limitations

This is an academic learning project, not a production storefront. It does not implement real authentication, payment processing, moderation, or production-grade authorization. Review usernames are display names rather than authenticated user foreign keys. Wishlist and library actions use the demo identity `DemoPlayer` in the current UI.
