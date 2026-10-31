"""HTTP API for the Next.js Steamish application.

Start with: python -m uvicorn backend.http_api:app --host 127.0.0.1 --port 8000 --reload
Apply sql/migrations/001_application_features.sql before first use.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import time
from typing import Literal

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field

from backend.db import connect, transaction
from backend.embeddings import embed

app = FastAPI(
    title="Steamish API",
    version="1.0.0",
    description="Catalogue, wishlist, review, analytics and vector recommendation API.",
)

APP_ENV = os.getenv("APP_ENV", "development").lower()
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-only-change-me")
SESSION_COOKIE = "steamish_session"
SESSION_TTL_SECONDS = 7 * 24 * 60 * 60
COOKIE_SECURE = APP_ENV == "production"

USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]{3,32}$")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
SORTS = {
    "title_asc": "g.title ASC",
    "title_desc": "g.title DESC",
    "newest": "g.created_at DESC, g.title ASC",
    "rating": "s.average_rating DESC NULLS LAST, s.genuine_review_count DESC, g.title ASC",
    "popular": "s.genuine_review_count DESC, g.title ASC",
}


class RegisterInput(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=10, max_length=128)


class LoginInput(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class ReviewInput(BaseModel):
    rating: int = Field(ge=1, le=5)
    body: str = Field(min_length=5, max_length=1000)


class GameInput(BaseModel):
    title: str = Field(min_length=1, max_length=140)
    description: str = Field(min_length=10, max_length=4000)
    genres: list[str] = Field(min_length=1, max_length=10)
    platforms: list[str] = Field(min_length=1, max_length=10)
    pricing_model: Literal["Free-to-play", "Paid", "Subscription"] = "Paid"
    cover_url: str | None = Field(default=None, max_length=1000)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _hash_password(password: str) -> str:
    """PBKDF2 hash using a fresh random salt; never store a plaintext password."""
    salt = secrets.token_bytes(16)
    rounds = 310_000
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
    return f"pbkdf2_sha256${rounds}${_b64(salt)}${_b64(derived)}"


def _verify_password(password: str, saved: str | None) -> bool:
    if not saved:
        return False
    try:
        algorithm, rounds_text, salt_text, derived_text = saved.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        rounds = int(rounds_text)
        if rounds < 100_000 or rounds > 2_000_000:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), _unb64(salt_text), rounds)
        return hmac.compare_digest(actual, _unb64(derived_text))
    except (ValueError, TypeError):
        return False


def _new_session(user_id: int) -> str:
    payload = f"{int(user_id)}.{int(time.time()) + SESSION_TTL_SECONDS}".encode("ascii")
    encoded = _b64(payload)
    signature = hmac.new(SESSION_SECRET.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def _session_user_id(token: str | None) -> int | None:
    if not token or "." not in token:
        return None
    try:
        encoded, signature = token.rsplit(".", 1)
        expected = hmac.new(SESSION_SECRET.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        user_id_text, expiry_text = _unb64(encoded).decode("ascii").split(".", 1)
        if int(expiry_text) <= int(time.time()):
            return None
        return int(user_id_text)
    except (ValueError, UnicodeDecodeError, TypeError):
        return None


def _set_session(response: Response, user_id: int) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=_new_session(user_id),
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def _user_view(row: dict | None) -> dict | None:
    if not row:
        return None
    return {"id": row["id"], "username": row["username"], "email": row.get("email"), "role": row["role"]}


def current_user(request: Request) -> dict | None:
    user_id = _session_user_id(request.cookies.get(SESSION_COOKIE))
    if user_id is None:
        return None
    c = connect()
    try:
        row = c.execute(
            "SELECT id, username, email, role FROM users WHERE id=%s",
            (user_id,),
        ).fetchone()
        return _user_view(row)
    finally:
        c.close()


def require_user(request: Request) -> dict:
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Sign in to use this feature.")
    return user


def require_admin(user: dict = Depends(require_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Administrator access is required.")
    return user


def _normalize_game_input(data: GameInput) -> tuple[str, str, list[str], list[str], str, str | None]:
    title = data.title.strip()
    description = data.description.strip()
    genres = list(dict.fromkeys(x.strip() for x in data.genres if x.strip()))
    platforms = list(dict.fromkeys(x.strip() for x in data.platforms if x.strip()))
    cover_url = data.cover_url.strip() if data.cover_url else None
    if not title or len(description) < 10 or not genres or not platforms:
        raise HTTPException(status_code=422, detail="Title, description, at least one genre, and at least one platform are required.")
    if cover_url and not re.match(r"^https?://", cover_url, re.I):
        raise HTTPException(status_code=422, detail="Cover URL must start with http:// or https://.")
    if any(len(v) > 40 for v in genres + platforms):
        raise HTTPException(status_code=422, detail="Each genre and platform must be 40 characters or fewer.")
    return title, description, genres, platforms, data.pricing_model, cover_url


def _embedding_text(title: str, description: str, genres: list[str], platforms: list[str]) -> str:
    return f"{title}. {description}. Genres: {', '.join(genres)}. Platforms: {', '.join(platforms)}."


def _vector_literal(text: str) -> str:
    return "[" + ",".join(str(float(x)) for x in embed(text)) + "]"


@app.get("/api/health")
def health() -> dict:
    try:
        c = connect()
        try:
            c.execute("SELECT 1")
        finally:
            c.close()
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable; check DATABASE_URL and PostgreSQL.") from exc


@app.post("/api/auth/register", status_code=201)
def register(data: RegisterInput, response: Response) -> dict:
    username = data.username.strip()
    email = data.email.strip().lower()
    if not USERNAME_RE.fullmatch(username):
        raise HTTPException(status_code=422, detail="Username must be 3–32 characters and use only letters, numbers, underscores, or hyphens.")
    if not EMAIL_RE.fullmatch(email):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    if len(data.password) < 10:
        raise HTTPException(status_code=422, detail="Password must contain at least 10 characters.")
    try:
        with transaction() as c:
            row = c.execute(
                "INSERT INTO users(username,email,password_hash,role) VALUES (%s,%s,%s,'player') RETURNING id,username,email,role",
                (username, email, _hash_password(data.password)),
            ).fetchone()
            c.execute("INSERT INTO demo_wallets(user_id, credits) VALUES (%s,100) ON CONFLICT(user_id) DO NOTHING", (row["id"],))
    except psycopg.errors.UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="That username or email is already registered.") from exc
    _set_session(response, row["id"])
    return {"user": _user_view(row)}


@app.post("/api/auth/login")
def login(data: LoginInput, response: Response) -> dict:
    email = data.email.strip().lower()
    c = connect()
    try:
        row = c.execute(
            "SELECT id,username,email,password_hash,role FROM users WHERE LOWER(email)=LOWER(%s)",
            (email,),
        ).fetchone()
    finally:
        c.close()
    if not row or not _verify_password(data.password, row.get("password_hash")):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    _set_session(response, row["id"])
    return {"user": _user_view(row)}


@app.post("/api/auth/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, secure=COOKIE_SECURE, samesite="lax")
    return {"ok": True}


@app.get("/api/auth/me")
def me(request: Request) -> dict:
    return {"user": current_user(request)}


@app.get("/api/games")
def list_games(
    q: str = Query(default="", max_length=100),
    genre: str = Query(default="", max_length=40),
    platform: str = Query(default="", max_length=40),
    pricing_model: str = Query(default="", max_length=30),
    min_rating: float = Query(default=0, ge=0, le=5),
    sort: str = Query(default="title_asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=48),
) -> dict:
    order_by = SORTS.get(sort)
    if not order_by:
        raise HTTPException(status_code=422, detail="Unsupported sort option.")
    where: list[str] = []
    args: list[object] = []
    if q.strip():
        term = "%" + q.strip().replace("%", r"\%").replace("_", r"\_") + "%"
        where.append("(g.title ILIKE %s OR g.description ILIKE %s)")
        args.extend([term, term])
    if genre:
        where.append("%s = ANY(g.genres)")
        args.append(genre)
    if platform:
        where.append("%s = ANY(g.platforms)")
        args.append(platform)
    if pricing_model:
        if pricing_model not in {"Free-to-play", "Paid", "Subscription"}:
            raise HTTPException(status_code=422, detail="Unsupported pricing model.")
        where.append("g.pricing_model=%s")
        args.append(pricing_model)
    if min_rating > 0:
        where.append("COALESCE(s.average_rating, 0) >= %s")
        args.append(min_rating)
    where_sql = " WHERE " + " AND ".join(where) if where else ""
    summary_join = """ LEFT JOIN (
        SELECT game_id,
               COUNT(*) FILTER (WHERE is_fictional=FALSE) AS genuine_review_count,
               AVG(rating) FILTER (WHERE is_fictional=FALSE) AS average_rating
        FROM reviews GROUP BY game_id
    ) s ON s.game_id=g.id """
    c = connect()
    try:
        total = c.execute("SELECT COUNT(*) AS n FROM games g" + summary_join + where_sql, args).fetchone()["n"]
        rows = c.execute(
            "SELECT g.id,g.title,g.description,g.genres,g.platforms,g.pricing_model,g.cover_url,g.created_at,"
            "COALESCE(s.genuine_review_count,0) AS review_count,s.average_rating "
            "FROM games g" + summary_join + where_sql + f" ORDER BY {order_by} LIMIT %s OFFSET %s",
            [*args, page_size, (page - 1) * page_size],
        ).fetchall()
        return {
            "games": [dict(r) for r in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }
    finally:
        c.close()


@app.get("/api/games/{game_id}")
def game_details(game_id: int) -> dict:
    c = connect()
    try:
        game = c.execute(
            """SELECT g.id,g.title,g.description,g.genres,g.platforms,g.pricing_model,g.cover_url,g.created_at,
                      COALESCE(s.genuine_review_count,0) AS review_count,s.average_genuine_rating AS average_rating
               FROM games g LEFT JOIN game_review_summary s ON s.game_id=g.id WHERE g.id=%s""",
            (game_id,),
        ).fetchone()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found.")
        reviews = c.execute(
            """SELECT id,username,rating,body,is_fictional,created_at
               FROM reviews WHERE game_id=%s ORDER BY created_at DESC LIMIT 50""",
            (game_id,),
        ).fetchall()
        return {**dict(game), "reviews": [dict(r) for r in reviews]}
    finally:
        c.close()


@app.post("/api/games/{game_id}/reviews")
def upsert_review(game_id: int, data: ReviewInput, user: dict = Depends(require_user)) -> dict:
    body = data.body.strip()
    if not 5 <= len(body) <= 1000:
        raise HTTPException(status_code=422, detail="Review must contain between 5 and 1000 characters.")
    with transaction() as c:
        if not c.execute("SELECT id FROM games WHERE id=%s FOR SHARE", (game_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Game not found.")
        row = c.execute(
            """INSERT INTO reviews(user_id,game_id,username,rating,body,is_fictional)
               VALUES (%s,%s,%s,%s,%s,FALSE)
               ON CONFLICT (user_id,game_id) WHERE user_id IS NOT NULL
               DO UPDATE SET username=EXCLUDED.username,rating=EXCLUDED.rating,body=EXCLUDED.body,
                             is_fictional=FALSE,created_at=NOW()
               RETURNING id,username,rating,body,is_fictional,created_at""",
            (user["id"], game_id, user["username"], data.rating, body),
        ).fetchone()
    return {"review": dict(row)}


@app.get("/api/wishlist")
def get_wishlist(user: dict = Depends(require_user)) -> dict:
    c = connect()
    try:
        rows = c.execute(
            """SELECT g.id,g.title,g.description,g.genres,g.platforms,g.pricing_model,g.cover_url,g.created_at,w.added_at
               FROM wishlist w JOIN games g ON g.id=w.game_id
               WHERE w.user_id=%s ORDER BY w.added_at DESC,g.title""",
            (user["id"],),
        ).fetchall()
        return {"games": [dict(r) for r in rows]}
    finally:
        c.close()


@app.post("/api/wishlist/{game_id}", status_code=201)
def add_wishlist(game_id: int, user: dict = Depends(require_user)) -> dict:
    with transaction() as c:
        if not c.execute("SELECT id FROM games WHERE id=%s", (game_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Game not found.")
        c.execute(
            "INSERT INTO wishlist(user_id,game_id) VALUES (%s,%s) ON CONFLICT(user_id,game_id) DO NOTHING",
            (user["id"], game_id),
        )
    return {"ok": True, "message": "Saved to wishlist."}


@app.delete("/api/wishlist/{game_id}")
def delete_wishlist(game_id: int, user: dict = Depends(require_user)) -> dict:
    with transaction() as c:
        c.execute("DELETE FROM wishlist WHERE user_id=%s AND game_id=%s", (user["id"], game_id))
    return {"ok": True}


@app.get("/api/library")
def get_library(user: dict = Depends(require_user)) -> dict:
    c = connect()
    try:
        rows = c.execute(
            """SELECT g.id,g.title,g.description,g.genres,g.platforms,g.pricing_model,g.cover_url,g.created_at,l.added_at
               FROM user_library l JOIN games g ON g.id=l.game_id
               WHERE l.user_id=%s ORDER BY l.added_at DESC,g.title""",
            (user["id"],),
        ).fetchall()
        return {"games": [dict(r) for r in rows]}
    finally:
        c.close()


@app.post("/api/library/{game_id}", status_code=201)
def add_library(game_id: int, user: dict = Depends(require_user)) -> dict:
    with transaction() as c:
        if not c.execute("SELECT id FROM games WHERE id=%s", (game_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Game not found.")
        c.execute(
            "INSERT INTO user_library(user_id,game_id) VALUES (%s,%s) ON CONFLICT(user_id,game_id) DO NOTHING",
            (user["id"], game_id),
        )
    return {"ok": True, "message": "Added to your library."}


@app.delete("/api/library/{game_id}")
def delete_library(game_id: int, user: dict = Depends(require_user)) -> dict:
    with transaction() as c:
        c.execute("DELETE FROM user_library WHERE user_id=%s AND game_id=%s", (user["id"], game_id))
    return {"ok": True}


@app.get("/api/recommendations")
def recommendations(
    game_id: int | None = Query(default=None, ge=1),
    q: str = Query(default="", min_length=0, max_length=500),
    limit: int = Query(default=8, ge=1, le=20),
) -> dict:
    c = connect()
    try:
        if game_id is not None:
            game = c.execute("SELECT id,title,description,genres,platforms FROM games WHERE id=%s", (game_id,)).fetchone()
            if not game:
                raise HTTPException(status_code=404, detail="Reference game not found.")
            text = _embedding_text(game["title"], game["description"], list(game["genres"] or []), list(game["platforms"] or []))
            vector = _vector_literal(text)
            rows = c.execute(
                """SELECT g.id,g.title,g.description,g.genres,g.platforms,g.pricing_model,g.cover_url,
                          1-(g.embedding <=> %s::vector) AS similarity
                   FROM games g WHERE g.id<>%s AND g.embedding IS NOT NULL
                   ORDER BY g.embedding <=> %s::vector,g.title LIMIT %s""",
                (vector, game_id, vector, limit),
            ).fetchall()
            source = {"type": "game", "game_id": game_id, "title": game["title"]}
        else:
            if len(q.strip()) < 3:
                raise HTTPException(status_code=422, detail="Enter at least three characters describing the games you like.")
            vector = _vector_literal(q.strip()[:500])
            rows = c.execute(
                """SELECT g.id,g.title,g.description,g.genres,g.platforms,g.pricing_model,g.cover_url,
                          1-(g.embedding <=> %s::vector) AS similarity
                   FROM games g WHERE g.embedding IS NOT NULL
                   ORDER BY g.embedding <=> %s::vector,g.title LIMIT %s""",
                (vector, vector, limit),
            ).fetchall()
            source = {"type": "description"}
        return {
            "source": source,
            "games": [{**dict(r), "similarity": round(float(r["similarity"]), 4)} for r in rows],
        }
    finally:
        c.close()


@app.get("/api/analytics")
def analytics() -> dict:
    c = connect()
    try:
        overview = c.execute(
            """SELECT
                 (SELECT COUNT(*) FROM games) AS total_games,
                 (SELECT COUNT(*) FROM reviews WHERE is_fictional=FALSE) AS genuine_reviews,
                 (SELECT COUNT(*) FROM users WHERE password_hash IS NOT NULL) AS registered_users,
                 (SELECT COUNT(*) FROM wishlist) AS wishlist_entries"""
        ).fetchone()
        genres = c.execute(
            "SELECT item.genre AS name,COUNT(*) AS count FROM games g "
            "CROSS JOIN LATERAL UNNEST(g.genres) AS item(genre) "
            "GROUP BY item.genre ORDER BY count DESC,name"
        ).fetchall()
        platforms = c.execute(
            "SELECT item.platform AS name,COUNT(*) AS count FROM games g "
            "CROSS JOIN LATERAL UNNEST(g.platforms) AS item(platform) "
            "GROUP BY item.platform ORDER BY count DESC,name"
        ).fetchall()
        top_rated = c.execute(
            """SELECT g.id,g.title,ROUND(AVG(r.rating)::numeric,2) AS average_rating,COUNT(r.id) AS review_count
               FROM games g JOIN reviews r ON r.game_id=g.id AND r.is_fictional=FALSE
               GROUP BY g.id,g.title HAVING COUNT(r.id)>=2
               ORDER BY AVG(r.rating) DESC,COUNT(r.id) DESC,g.title LIMIT 8"""
        ).fetchall()
        most_reviewed = c.execute(
            """SELECT g.id,g.title,COUNT(r.id) AS review_count
               FROM games g JOIN reviews r ON r.game_id=g.id AND r.is_fictional=FALSE
               GROUP BY g.id,g.title ORDER BY review_count DESC,g.title LIMIT 8"""
        ).fetchall()
        return {
            "overview": dict(overview),
            "genres": [dict(r) for r in genres],
            "platforms": [dict(r) for r in platforms],
            "top_rated": [dict(r) for r in top_rated],
            "most_reviewed": [dict(r) for r in most_reviewed],
        }
    finally:
        c.close()


@app.post("/api/admin/games", status_code=201)
def admin_create_game(data: GameInput, user: dict = Depends(require_admin)) -> dict:
    title, description, genres, platforms, pricing_model, cover_url = _normalize_game_input(data)
    vector = _vector_literal(_embedding_text(title, description, genres, platforms))
    try:
        with transaction() as c:
            row = c.execute(
                """INSERT INTO games(title,description,genres,platforms,pricing_model,embedding,cover_url)
                   VALUES (%s,%s,%s,%s,%s,%s::vector,%s)
                   RETURNING id,title,description,genres,platforms,pricing_model,cover_url,created_at""",
                (title, description, genres, platforms, pricing_model, vector, cover_url),
            ).fetchone()
    except psycopg.errors.UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="A game with that title already exists.") from exc
    return {"game": dict(row)}


@app.put("/api/admin/games/{game_id}")
def admin_update_game(game_id: int, data: GameInput, user: dict = Depends(require_admin)) -> dict:
    title, description, genres, platforms, pricing_model, cover_url = _normalize_game_input(data)
    vector = _vector_literal(_embedding_text(title, description, genres, platforms))
    try:
        with transaction() as c:
            row = c.execute(
                """UPDATE games SET title=%s,description=%s,genres=%s,platforms=%s,pricing_model=%s,
                          embedding=%s::vector,cover_url=%s
                   WHERE id=%s
                   RETURNING id,title,description,genres,platforms,pricing_model,cover_url,created_at""",
                (title, description, genres, platforms, pricing_model, vector, cover_url, game_id),
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Game not found.")
    except psycopg.errors.UniqueViolation as exc:
        raise HTTPException(status_code=409, detail="A game with that title already exists.") from exc
    return {"game": dict(row)}


@app.delete("/api/admin/games/{game_id}")
def admin_delete_game(game_id: int, user: dict = Depends(require_admin)) -> dict:
    with transaction() as c:
        row = c.execute("DELETE FROM games WHERE id=%s RETURNING id", (game_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Game not found.")
    return {"ok": True}


if APP_ENV == "production" and SESSION_SECRET == "dev-only-change-me":
    raise RuntimeError("Set a strong SESSION_SECRET before running in production.")
