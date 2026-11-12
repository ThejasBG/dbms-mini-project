# Application Testing Results

Tested on 2026-10-31. The existing local `game_catalog` database was not
recreated or used for the fresh-initialization test. `backend.test_db` uses
temporary transactional test records and verifies rollback.

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
- A disposable account completed registration, login/logout, player-role
  denial at `/admin`, wishlist/library add-view-remove, and review submission
  and update. The account, review, and collection entries were removed; a
  follow-up database check found no test account or review.
- The README database setup was tested in a separate disposable PostgreSQL
  database: pgvector was enabled, the schema seeded 53 games with 384D
  embeddings, the migration applied, `backend.test_db` passed, and a temporary
  API instance returned `database: connected`. The disposable database was
  dropped afterward; `game_catalog` remained intact with 53 games.

- Admin API workflow, using a disposable account promoted to `admin`: player
  create denied (403); admin create (201), update (200), duplicate title (409),
  invalid cover URL (422), delete (200), repeat delete (404). The disposable
  account and game were removed; the catalogue still had 53 games.
- The migration was re-applied (`DROP VIEW IF EXISTS` + `CREATE VIEW`) and the
  view returned 53 rows. The `CREATE`/`ALTER`/`DROP` demo in `sql/queries.sql`
  (section 14) ran on a temporary table.
- The backend now raises a clear error if `DATABASE_URL` or `SESSION_SECRET`
  is unset; `backend.test_http_api` (3 tests) passes with them configured.

## Not verified in this pass

- Admin catalogue actions were tested through the API only, not through the
  browser admin page.
- Python/Node dependencies were already installed, so a clean dependency
  installation and a fresh frontend-server restart were not repeated.
- Instructor confirmation of the Next.js requirement and the project's
  uniqueness within the section still need human confirmation.

## Screenshots

- [Catalogue homepage](screenshots/catalogue-home.jpg)
- [Game details](screenshots/game-details.jpg)
- [Analytics](screenshots/analytics.jpg)
- [Vector recommendations](screenshots/vector-recommendations.jpg)
