# Steamish ER diagram

This diagram reflects `sql/schema.sql` plus the application-specific migration at `sql/migrations/001_application_features.sql`. Re-export/update it if the schema changes again.

```mermaid
erDiagram
    USERS ||--o{ USER_LIBRARY : owns
    GAMES ||--o{ USER_LIBRARY : appears_in
    USERS ||--o{ WISHLIST : saves
    GAMES ||--o{ WISHLIST : wished_for
    USERS o|--o{ REVIEWS : writes
    GAMES ||--o{ REVIEWS : receives
    USERS ||--o| DEMO_WALLETS : has

    USERS {
        bigint id PK
        text username UK
        text email UK
        text password_hash
        text role
        timestamptz created_at
    }
    GAMES {
        bigint id PK
        text title UK
        text description
        text_array genres
        text_array platforms
        text pricing_model
        vector_384 embedding
        text cover_url
        timestamptz created_at
    }
    REVIEWS {
        bigint id PK
        bigint user_id FK "nullable for legacy/seed reviews"
        bigint game_id FK
        text username
        smallint rating
        text body
        boolean is_fictional
        timestamptz created_at
    }
    USER_LIBRARY {
        bigint user_id PK,FK
        bigint game_id PK,FK
        timestamptz added_at
    }
    WISHLIST {
        bigint user_id PK,FK
        bigint game_id PK,FK
        timestamptz added_at
    }
    DEMO_WALLETS {
        bigint user_id PK,FK
        integer credits
    }
```

## Notes

- `users.username` and `users.email` are protected by case-insensitive unique indexes. Existing demo users have no email or password hash and cannot sign in until a real account is registered.
- `user_library` and `wishlist` use composite primary keys `(user_id, game_id)`, preventing duplicate entries for a given account.
- New reviews reference an authenticated user through nullable `reviews.user_id`. The username field remains a display-name snapshot. Legacy and fictional seed reviews may have `user_id = NULL`.
- `reviews_user_game_uq` allows one review per registered user/game pair; posting again updates the existing review.
- Game metadata has an optional `cover_url`. Embeddings remain stored in pgvector as 384-dimensional vectors.
- `ON DELETE CASCADE` is used for library/wishlist links and game reviews; reviewer account deletion sets `reviews.user_id` to null so the review record can remain attached to the game.
