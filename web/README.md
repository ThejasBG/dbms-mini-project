# Steamish Next.js application

This is the Next.js interface for the Steamish project. It calls the Python FastAPI service through a same-origin Next.js route handler, so the browser does not need direct access to PostgreSQL or to the internal API port.

## Prerequisites

- Node.js 22 or a later supported LTS release
- Python 3.11+
- PostgreSQL with the pgvector extension installed

## Setup

1. From the repository root, install Python dependencies and initialise the existing project database:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python -m backend.init_db
   ```

2. Apply the application migration after the tables have been initialised:

   ```powershell
   psql -U postgres -d game_catalog -f sql/migrations/001_application_features.sql
   ```

   Use the database username/name that matches `DATABASE_URL` in your `.env`.

3. Copy the root `.env.example` to `.env`. Replace `DATABASE_URL` with your local database connection string. Generate a local session signing key with:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   Put the generated value in `SESSION_SECRET` in the root `.env`. Do not commit `.env`.

4. Start the API from the repository root in Terminal 1:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   python -m uvicorn backend.http_api:app --host 127.0.0.1 --port 8000 --reload
   ```

   Check `http://127.0.0.1:8000/api/health` for a database status response.

5. In Terminal 2, install the Next.js dependencies and run the frontend:

   ```powershell
   cd web
   Copy-Item .env.example .env.local
   npm install
   npm run dev
   ```

   Open `http://localhost:3000`.

## Create an administrator account

1. Register through `/register` with the account that should administer the catalogue.
2. In psql, promote that account explicitly (replace the sample address):

   ```sql
   UPDATE users SET role = 'admin' WHERE LOWER(email) = LOWER('admin@example.com');
   ```

3. Sign out and sign in again, then open `/admin`.

Do not promote untrusted accounts. The API checks the role on the server for every catalogue-management operation; hiding the Admin link alone is not the security control.

## Application features

- Paginated catalogue search with genre, platform, pricing-model, and minimum-rating filters
- Sorting by title, recency, genuine review count, or rating
- Game detail pages with review summaries and submission
- Account registration/sign-in with salted PBKDF2 password hashes and an HttpOnly signed session cookie
- Per-account wishlist and game library
- pgvector recommendations from a reference game or free-text taste description
- SQL-driven genre/platform analytics and top-rated/most-reviewed tables
- Administrator-only add/update/delete catalogue actions; each edit regenerates the game's embedding
- Server-side validation, SQL parameters, relational constraints, and useful empty/error states

## API design

The FastAPI service is `backend/http_api.py`. The Next.js catch-all route at `app/api/[...path]/route.ts` forwards browser requests to `STEAMISH_API_URL` (default `http://127.0.0.1:8000`) and forwards the session cookie. The API should remain bound to localhost for local development. Do not expose the Python API directly to the public internet without a proper deployment/security review.

## Notes

- The existing Streamlit interface in `../frontend/app.py` is retained as a fallback while the Next.js application is verified.
- Demo-credit functionality remains in the legacy Streamlit prototype and is not a payment feature.
- Recommendation similarity is a vector-distance score, not a probability of user satisfaction.
- Cover URLs are optional metadata; a stylised placeholder is shown when no cover is configured.
- The app requires the migration that adds account columns, reviewer account references, cover URLs, and the review summary view.

## Checks before submission

From the `web/` directory, run:

```powershell
npm run typecheck
npm run build
```

From the repository root, run:

```powershell
python -m backend.test_http_api
python -m backend.test_db
```

The database integration test requires an initialised PostgreSQL/pgvector database. Run the application smoke tests against the actual running app and record the results in `../docs/TESTING_RESULTS.md`. Capture screenshots from the working application for the project submission.
