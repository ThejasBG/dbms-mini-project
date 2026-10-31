import json
from backend.db import connect, transaction, clean_game
from backend.embeddings import embed
from backend.cache import get, put, invalidate

def list_games(f=None):
    f=f or {}; key="catalog:"+json.dumps(f,sort_keys=True)
    hit=get(key)
    if hit is not None: return {"games":hit,"cached":True}
    clauses=[]; args=[]
    if f.get("genre"): clauses.append("%s = ANY(genres)"); args.append(f["genre"])
    if f.get("platform"): clauses.append("%s = ANY(platforms)"); args.append(f["platform"])
    if f.get("query"):
        clauses.append("(title ILIKE %s OR description ILIKE %s)")
        term="%"+f["query"][:100]+"%"; args.extend([term,term])
    where=" WHERE "+" AND ".join(clauses) if clauses else ""
    c=connect()
    try: games=[clean_game(r) for r in c.execute("SELECT id,title,description,genres,platforms,pricing_model,created_at FROM games"+where+" ORDER BY title LIMIT 250",args).fetchall()]
    finally: c.close()
    put(key,games); return {"games":games,"cached":False}

def details(gid):
    c=connect()
    try:
        g=c.execute("SELECT id,title,description,genres,platforms,pricing_model,created_at FROM games WHERE id=%s",(int(gid),)).fetchone()
        if not g: return {"error":"Game not found"}
        d=clean_game(g)
        d["reviews"]=[{**dict(r),"created_at":r["created_at"].isoformat()} for r in c.execute("SELECT username,rating,body,is_fictional,created_at FROM reviews WHERE game_id=%s ORDER BY created_at DESC LIMIT 20",(int(gid),)).fetchall()]
        return d
    finally: c.close()

def recommend(gid=None, query=None, limit=8):
    limit=max(1,min(int(limit),20)); c=connect()
    try:
        if gid:
            g=c.execute("SELECT id,title,description,genres,platforms FROM games WHERE id=%s",(int(gid),)).fetchone()
            if not g: return {"error":"Game not found"}
            q=f"{g['title']} {g['description']} genres {' '.join(g['genres'])}"; v=embed(q)
            # psycopg adapts a Python list as double precision[], so serialize it
            # as pgvector's textual format and cast each placeholder to vector.
            vector_param='[' + ','.join(str(float(x)) for x in v) + ']'
            rows=c.execute("SELECT id,title,description,genres,platforms,pricing_model,1-(embedding <=> %s::vector) similarity FROM games WHERE id<>%s ORDER BY embedding <=> %s::vector LIMIT %s",(vector_param,int(gid),vector_param,limit)).fetchall()
        else:
            v=embed((query or "popular games").strip()[:500])
            vector_param='[' + ','.join(str(float(x)) for x in v) + ']'
            rows=c.execute("SELECT id,title,description,genres,platforms,pricing_model,1-(embedding <=> %s::vector) similarity FROM games ORDER BY embedding <=> %s::vector LIMIT %s",(vector_param,vector_param,limit)).fetchall()
        return {"games":[{**clean_game(r),"similarity":round(float(r["similarity"]),4)} for r in rows]}
    finally: c.close()

def add_review(gid,username,rating,body):
    username=(username or "").strip()[:40]; body=(body or "").strip(); rating=int(rating)
    if not username or not 5<=len(body)<=1000 or not 1<=rating<=5: return {"error":"Enter a username, 5–1000 character review, and rating from 1 to 5."}
    with transaction() as c:
        if not c.execute("SELECT id FROM games WHERE id=%s FOR SHARE",(int(gid),)).fetchone(): return {"error":"Game not found"}
        c.execute("INSERT INTO reviews(game_id,username,rating,body,is_fictional) VALUES (%s,%s,%s,%s,FALSE)",(int(gid),username,rating,body))
    invalidate(); return {"ok":True,"message":"Review saved."}

def add_library(username,gid):
    username=(username or "").strip()[:40]
    if not username: return {"error":"Username required"}
    with transaction() as c:
        u=c.execute("INSERT INTO users(username) VALUES (%s) ON CONFLICT(username) DO UPDATE SET username=EXCLUDED.username RETURNING id",(username,)).fetchone()
        c.execute("INSERT INTO user_library(user_id,game_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",(u["id"],int(gid)))
    return {"ok":True,"message":"Added to library."}

def list_library(username="DemoPlayer"):
    username=(username or "DemoPlayer").strip()[:40]
    c=connect()
    try:
        rows=c.execute("""SELECT g.id,g.title,g.description,g.genres,g.platforms,g.pricing_model,g.created_at
                         FROM users u JOIN user_library l ON l.user_id=u.id
                         JOIN games g ON g.id=l.game_id
                         WHERE u.username=%s ORDER BY l.added_at DESC, g.title""",(username,)).fetchall()
        return {"games":[clean_game(r) for r in rows]}
    finally: c.close()


def add_wishlist(username, gid):
    username = (username or "").strip()[:40]
    if not username:
        return {"error": "Username required."}
    with transaction() as c:
        u = c.execute(
            "INSERT INTO users(username) VALUES (%s) ON CONFLICT(username) DO UPDATE SET username=EXCLUDED.username RETURNING id",
            (username,),
        ).fetchone()
        if not c.execute("SELECT id FROM games WHERE id=%s", (int(gid),)).fetchone():
            return {"error": "Game not found."}
        c.execute(
            "INSERT INTO wishlist(user_id,game_id) VALUES (%s,%s) ON CONFLICT(user_id,game_id) DO NOTHING",
            (u["id"], int(gid)),
        )
    return {"ok": True, "message": "Added to wishlist."}


def remove_wishlist(username, gid):
    username = (username or "").strip()[:40]
    if not username:
        return {"error": "Username required."}
    with transaction() as c:
        row = c.execute("SELECT id FROM users WHERE username=%s", (username,)).fetchone()
        if not row:
            return {"ok": True, "message": "Wishlist item removed."}
        c.execute("DELETE FROM wishlist WHERE user_id=%s AND game_id=%s", (row["id"], int(gid)))
    return {"ok": True, "message": "Wishlist item removed."}


def list_wishlist(username="DemoPlayer"):
    username = (username or "DemoPlayer").strip()[:40]
    c = connect()
    try:
        rows = c.execute("""SELECT g.id,g.title,g.description,g.genres,g.platforms,g.pricing_model,g.created_at
                            FROM users u JOIN wishlist w ON w.user_id=u.id
                            JOIN games g ON g.id=w.game_id
                            WHERE u.username=%s ORDER BY w.added_at DESC, g.title""", (username,)).fetchall()
        return {"games": [clean_game(r) for r in rows]}
    finally:
        c.close()


def wallets():
    c=connect()
    try: return {"wallets":[dict(r) for r in c.execute("SELECT u.username,w.credits FROM users u JOIN demo_wallets w ON w.user_id=u.id WHERE u.username IN ('DemoPlayer','DemoFriend') ORDER BY u.username").fetchall()]}
    finally: c.close()

def transfer(src,dst,amount):
    amount=int(amount)
    if amount<1 or amount>100 or src==dst: return {"error":"Use a 1–100 credit transfer between different demo users."}
    with transaction() as c:
        users=c.execute("SELECT id,username FROM users WHERE username=ANY(%s) ORDER BY id FOR UPDATE",([src,dst],)).fetchall()
        ids={u["username"]:u["id"] for u in users}
        if src not in ids or dst not in ids: return {"error":"Use DemoPlayer and DemoFriend."}
        order=sorted([ids[src],ids[dst]])
        ws=c.execute("SELECT user_id,credits FROM demo_wallets WHERE user_id=ANY(%s) ORDER BY user_id FOR UPDATE",(order,)).fetchall()
        balances={w["user_id"]:w["credits"] for w in ws}
        if balances.get(ids[src],0)<amount: return {"error":"Insufficient demo credits."}
        c.execute("UPDATE demo_wallets SET credits=credits-%s WHERE user_id=%s",(amount,ids[src]))
        c.execute("UPDATE demo_wallets SET credits=credits+%s WHERE user_id=%s",(amount,ids[dst]))
    return {"ok":True,"message":f"Transferred {amount} demo credits atomically."}

def handle(r):
    try:
        a=r.get("action")
        if a=="list_games": return list_games(r.get("filters"))
        if a=="game_details": return details(r.get("game_id"))
        if a=="recommendations": return recommend(r.get("game_id"),r.get("query"),r.get("limit",8))
        if a=="add_review": return add_review(r.get("game_id"),r.get("username"),r.get("rating"),r.get("body"))
        if a=="add_to_library": return add_library(r.get("username"),r.get("game_id"))
        if a=="list_library": return list_library(r.get("username", "DemoPlayer"))
        if a=="add_to_wishlist": return add_wishlist(r.get("username", "DemoPlayer"), r.get("game_id"))
        if a=="remove_from_wishlist": return remove_wishlist(r.get("username", "DemoPlayer"), r.get("game_id"))
        if a=="list_wishlist": return list_wishlist(r.get("username", "DemoPlayer"))
        if a=="get_wallets": return wallets()
        if a=="transfer_demo_credits": return transfer(r.get("from_username"),r.get("to_username"),r.get("amount"))
        return {"error":"Unknown action"}
    except Exception as e:
        print(type(e).__name__,str(e)); return {"error":"Request failed; inspect backend logs."}
