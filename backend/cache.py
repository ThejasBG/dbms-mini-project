import json, redis
from backend.config import REDIS_URL
try:
    client = redis.Redis.from_url(REDIS_URL,decode_responses=True,socket_connect_timeout=1)
    client.ping()
except Exception:
    client = None
    print("Redis unavailable; continuing without cache.")
def get(key):
    try:
        x = client.get(key) if client else None
        return json.loads(x) if x else None
    except Exception: return None
def put(key,value):
    try:
        if client: client.setex(key,90,json.dumps(value,default=str))
    except Exception: pass
def invalidate():
    try:
        if client:
            for k in client.scan_iter("catalog:*"): client.delete(k)
    except Exception: pass
