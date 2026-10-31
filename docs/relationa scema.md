# Steamish ER diagram

The diagram below mirrors `sql/schema.sql`.

```mermaid
erDiagram
    USERS ||--o{ USER_LIBRARY : owns
    GAMES ||--o{ USER_LIBRARY : appears_in
    USERS ||--o{ WISHLIST : saves
    GAMES ||--o{ WISHLIST : wished_for
    GAMES ||--o{ REVIEWS : receives
    USERS ||--o| DEMO_WALLETS : has

    USERS {
        bigint id PK
        text username UK
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
        timestamptz created_at
    }
    REVIEWS {
        bigint id PK
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

Notes:
- `user_library` and `wishlist` use composite primary keys `(user_id, game_id)`, preventing duplicate entries.
- Reviews are associated with a game and retain a display-name string for the reviewer; there is no account/authentication relationship for reviewers in this learning project.
- All foreign keys to users/games cascade on delete.
