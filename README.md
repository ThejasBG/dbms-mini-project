# Steamish — Game Discovery and Recommendation System

Steamish is a game-discovery application that combines a structured PostgreSQL catalogue with vector-powered content recommendations using pgvector. It stores game metadata and review text, not game files.

## Application versions

- **Next.js application (recommended for the course requirements):** `web/`
- **FastAPI HTTP API:** `backend/http_api.py`
- **Existing Streamlit prototype (kept as a fallback during migration):** `frontend/app.py`

The Next.js application adds paginated discovery, multi-field filtering, account registration/sign-in, per-account wishlists and libraries, user-linked reviews, recommendations, database-powered analytics, and administrator-only catalogue management.

## Requirements

- Python 3.11 or newer
- Node.js 22 or a later supported LTS release
- PostgreSQL with a pgvector build compatible with that PostgreSQL version

## Setup the database

1. Install PostgreSQL and pgvector. Create `game_catalog` if it does not already exist and enable the extension:

   ```sql
   CREATE DATABASE game_catalog;
   -- Connect to game_catalog before running:
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. Copy `.env.example` to `.env`, and set `DATABASE_URL` to your actual PostgreSQL connection string. Do not commit `.env`.

3. Create a Python environment and install dependencies from the repository root:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Initialise/seed the current database schema:

   ```powershell
   python -m backend.init_db
   ```

   The starter seeds 53 games, embeddings, demo users, and fictional demonstration reviews. The first run may download the Sentence Transformers model. PostgreSQL remains the source of truth.

5. Apply the idempotent migration required by the Next.js application:

   ```powershell
   psql -U postgres -d game_catalog -f sql/migrations/001_application_features.sql
   ```

   Replace the database user/name as needed to match `DATABASE_URL`. This migration adds account fields and role support, connects new reviews to user accounts, adds optional cover URLs, and creates the review summary view.

## Run the Next.js application

1. Generate a random session signing secret:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   Put the generated value in `SESSION_SECRET` in the root `.env`. The included `dev-only-change-me` value is for local development only. Set a unique value before using any shared deployment.

2. Start the HTTP API in Terminal 1 from the repository root:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   python -m uvicorn backend.http_api:app --host 127.0.0.1 --port 8000 --reload
   ```

   Check `http://127.0.0.1:8000/api/health` for a database connection status.

3. Start Next.js in Terminal 2:

   ```powershell
   cd web
   Copy-Item .env.example .env.local
   npm install
   npm run dev
   ```

   Open `http://localhost:3000`.

The catch-all Next.js API route forwards requests to the Python API and passes the session cookie. In local development the API is bound to `127.0.0.1` intentionally. Do not expose it publicly without further deployment and security review.

## Create an administrator account

1. Register the account via `/register`.
2. Promote that trusted account from psql:

   ```sql
   UPDATE users SET role = 'admin' WHERE LOWER(email) = LOWER('admin@example.com');
   ```

3. Sign out and sign in again, then visit `/admin`.

New accounts have the `player` role. The backend checks the administrator role for catalogue changes; hiding the Admin link in the UI is not the security control. Do not promote untrusted accounts.

## Application features

- Search game titles/descriptions with genre, platform, pricing-model, and minimum-rating filters
- Sorting by title, recency, genuine review count, or rating
- Pagination backed by parameterised PostgreSQL queries
- Game detail pages with review summaries and review submission/update
- Account registration/sign-in with salted PBKDF2 password hashes and an HttpOnly, signed session cookie
- Per-account wishlist and game library with duplicate prevention and removal
- Content-based recommendations using 384-dimensional embeddings and pgvector cosine distance
- SQL-powered insights for genre/platform distributions, top-rated games, and most-reviewed games
- Administrator-only catalogue create/update/delete; edits regenerate embeddings
- PostgreSQL constraints, views, joins, aggregation, transactions, and indexes through the existing schema/features

## Database documentation and tests

| Requirement | Evidence |
|---|---|
| PostgreSQL schema | `sql/schema.sql` |
| Application migration | `sql/migrations/001_application_features.sql` |
| ER diagram | `docs/ER_DIAGRAM.md` |
| Advanced DB concepts | `docs/ADVANCED_DATABASE_CONCEPTS.md` |
| Important queries | `sql/queries.sql` and `sql/verify_schema.sql` |
| Schema/database checks | `python -m backend.test_db` |
| HTTP API authentication helper checks | `python -m backend.test_http_api` |
| Next.js application instructions | `web/README.md` |

Run the SQL checks in psql:

```powershell
psql -U postgres -d game_catalog -f sql/verify_schema.sql
psql -U postgres -d game_catalog -f sql/queries.sql
python -m backend.test_db
python -m backend.test_http_api
```

Before submission, also run `npm run typecheck` and `npm run build` from `web/`, and record the actual application smoke-test results in `docs/TESTING_RESULTS.md`.

## Streamlit fallback

The previous Streamlit UI remains available while the Next.js migration is verified. Start the legacy TCP service in Terminal 1:

```powershell
python -m backend.server
```

Then run in Terminal 2 from the repository root:

```powershell
streamlit run frontend/app.py
```

Its `DemoPlayer` wishlist/library and demo-credit transfer are learning demonstrations. The authenticated Next.js application uses real account IDs for wishlist/library/review ownership.

## Notes and limitations

- Seed reviews are fictional and excluded from genuine rating summaries and analytics.
- A vector similarity score is not a probability of user satisfaction.
- Artwork URLs are optional catalogue metadata; generated CSS art is shown when a cover is absent.
- Email verification, password recovery, rate limiting, review moderation workflow, production deployment hardening, monitoring, and backups remain future work. This is an academic learning project, not a production storefront.
