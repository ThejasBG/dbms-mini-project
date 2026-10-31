# Steamish Game Recommender --- Chen ER Diagram

This diagram uses traditional Chen notation:

-   Rectangles represent entities.
-   Diamonds represent relationships.
-   Ovals represent attributes.
-   Underlined attributes are primary keys (PK).
-   `1` and `N` indicate relationship cardinality.

## 1. Chen-style ER diagram

``` mermaid
flowchart TB
    U[USERS]
    G[GAMES]
    R[REVIEWS]
    L[USER_LIBRARY]
    W[WISHLIST]
    D[DEMO_WALLETS]

    WR{WRITES}
    RG{ABOUT}
    OW{HAS_LIBRARY_ENTRY}
    LG{REFERENCES_GAME}
    SW{SAVES_TO_WISHLIST}
    WG{WISHLISTS_GAME}
    HW{HAS_WALLET}

    U ---|1| WR
    WR ---|N| R
    R ---|N| RG
    RG ---|1| G

    U ---|1| OW
    OW ---|N| L
    L ---|N| LG
    LG ---|1| G

    U ---|1| SW
    SW ---|N| W
    W ---|N| WG
    WG ---|1| G

    U ---|1| HW
    HW ---|1| D

    classDef entity fill:#e8f0fe,stroke:#2457a6,stroke-width:2px,color:#111
    classDef relationship fill:#fff2cc,stroke:#a66b00,stroke-width:2px,color:#111
    class U,G,R,L,W,D entity
    class WR,RG,OW,LG,SW,WG,HW relationship
```

## 2. Entity attributes

Draw each attribute below as an oval connected to its entity rectangle.
Underline every primary-key attribute.

### USERS

-   `<u>`{=html}user_id`</u>`{=html} --- primary key
-   username
-   email
-   password_hash

### GAMES

-   `<u>`{=html}game_id`</u>`{=html} --- primary key
-   title
-   description
-   genres
-   platforms
-   embedding

### REVIEWS

-   `<u>`{=html}review_id`</u>`{=html} --- primary key
-   user_id --- foreign key referencing `USERS.user_id`
-   game_id --- foreign key referencing `GAMES.game_id`
-   rating
-   comment
-   created_at

### USER_LIBRARY

-   `<u>`{=html}library_id`</u>`{=html} --- primary key
-   user_id --- foreign key referencing `USERS.user_id`
-   game_id --- foreign key referencing `GAMES.game_id`
-   status

### WISHLIST

-   `<u>`{=html}wishlist_id`</u>`{=html} --- primary key
-   user_id --- foreign key referencing `USERS.user_id`
-   game_id --- foreign key referencing `GAMES.game_id`
-   created_at

### DEMO_WALLETS

-   `<u>`{=html}wallet_id`</u>`{=html} --- primary key
-   user_id --- foreign key referencing `USERS.user_id`
-   balance

## 3. Relationship cardinalities

  ---------------------------------------------------------------------------
  Relationship                           Cardinality Meaning
  --------------------- ---------------------------- ------------------------
  USERS --- WRITES ---                           1:N A user can write many
  REVIEWS                                            reviews; each review has
                                                     one author.

  GAMES --- ABOUT ---                            1:N A game can have many
  REVIEWS                                            reviews; each review is
                                                     about one game.

  USERS ---                                      1:N A user can have many
  HAS_LIBRARY_ENTRY ---                              library entries.
  USER_LIBRARY                                       

  GAMES ---                                      1:N A game can appear in
  REFERENCES_GAME ---                                many users' libraries.
  USER_LIBRARY                                       

  USERS ---                                      1:N A user can have many
  SAVES_TO_WISHLIST ---                              wishlist entries.
  WISHLIST                                           

  GAMES ---                                      1:N A game can appear on
  WISHLISTS_GAME ---                                 many users' wishlists.
  WISHLIST                                           

  USERS --- HAS_WALLET                           1:1 Each user has one
  --- DEMO_WALLETS                                   wallet, if
                                                     `DEMO_WALLETS.user_id`
                                                     is unique.
  ---------------------------------------------------------------------------

## 4. Conceptual many-to-many relationships

The two associative entities implement these conceptual relationships:

-   **USERS ↔ GAMES through USER_LIBRARY:** M:N. A user can have many
    games in their library, and a game can be in many users' libraries.
-   **USERS ↔ GAMES through WISHLIST:** M:N. A user can wishlist many
    games, and a game can be wishlisted by many users.

## 5. Notes before submitting

1.  Confirm the exact columns in your `sql/schema.sql`; this document
    reflects the project schema as previously described.
2.  The wallet relationship is 1:1 only if `DEMO_WALLETS.user_id` has a
    `UNIQUE` constraint (or is itself the primary key).
3.  If your actual schema has additional attributes or different names,
    update the attribute ovals to match it.
4.  `embedding` is included as an attribute of `GAMES`; you may omit it
    from a conceptual diagram if your instructor wants only
    business-level attributes.
