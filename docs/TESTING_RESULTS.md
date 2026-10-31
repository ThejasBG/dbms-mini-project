# Application Testing Results

Tested against the existing local `game_catalog` database on 2026-10-31. The
database was not recreated. `backend.test_db` uses temporary transactional test
records and verifies rollback.

## Automated checks

| Check | Result |
| --- | --- |
| `python -m backend.test_db` | PASS — required tables, pgvector/384D embeddings, constraints, foreign keys, and rollback |
| `python -m backend.test_http_api` | PASS — 3 authentication-helper tests |
| `npm.cmd run lint` | PASS |
| `npm.cmd run typecheck` | PASS |
| `npm.cmd run build` | PASS — Next.js production build completed |

## Live application checks

- API health returned `status: ok` and `database: connected`.
- Catalogue loaded 53 games. Previously verified catalogue interactions: Action
  genre filter (7 matches), search for “Hades” (1 match), title-descending sort,
  and page 2 pagination.
- Game details loaded, including game metadata and demo reviews. The page
  correctly distinguishes fictional seed reviews from genuine reviews.
- Analytics loaded database-derived catalogue, genre, and platform summaries.
- A natural-language recommendations query returned ranked results from
  pgvector, including similarity scores.
- Through the UI, registration created a `player` account and signed it in;
  signing out cleared the session, and a subsequent login succeeded.
- The player account was denied access to `/admin`.
- Wishlist and library entries were added, displayed, and removed through the
  UI. A review was submitted and updated; the genuine-review count stayed at
  one, confirming the one-review-per-account/game behavior.
- The disposable account, its review, and its collection data were removed.
  A database check confirmed no test account or test review remained.
- The README's running-app endpoints were smoke-checked: the API reported a
  connected database and the Next.js UI loaded on the documented local ports.

## Not verified in this pass

- Fresh database initialization was deliberately not run against the existing
  database. The README commands that initialize/seed the database were skipped
  to avoid changing existing data.
- The API and frontend were already running, so their processes were not
  stopped/restarted solely to rehearse the README launch commands.
- The Next.js requirement still needs instructor confirmation.

## Screenshots

- [Catalogue homepage](screenshots/catalogue-home.jpg)
- [Game details](screenshots/game-details.jpg)
- [Analytics](screenshots/analytics.jpg)
- [Vector recommendations](screenshots/vector-recommendations.jpg)
