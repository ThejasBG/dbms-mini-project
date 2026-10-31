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

## Not verified in this pass

- Fresh database initialization was deliberately not run against the existing
  database.
- Registration, login/logout, role-restricted admin actions, review submission,
  and wishlist/library mutations were not exercised because no disposable test
  account was authorized. Avoid using real accounts or leaving test records.
- The complete README startup procedure and instructor confirmation of the
  Next.js requirement still need human confirmation.

## Screenshots

- [Catalogue homepage](screenshots/catalogue-home.jpg)
- [Game details](screenshots/game-details.jpg)
- [Analytics](screenshots/analytics.jpg)
- [Vector recommendations](screenshots/vector-recommendations.jpg)
