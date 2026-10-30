from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row
from pgvector.psycopg import register_vector
from backend.config import DATABASE_URL

def connect():
    c = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    register_vector(c)
    return c

@contextmanager
def transaction():
    c = connect()
    try:
        with c.transaction():
            yield c
    finally:
        c.close()

def clean_game(r):
    if not r: return None
    d = dict(r); d.pop("embedding", None)
    d["genres"] = list(d.get("genres") or []); d["platforms"] = list(d.get("platforms") or [])
    if d.get("created_at"): d["created_at"] = d["created_at"].isoformat()
    return d
