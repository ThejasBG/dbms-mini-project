from pathlib import Path
from backend.db import connect
from backend.catalog_seed import GAMES, REVIEWS
from backend.embeddings import embed

def main():
    conn = connect()
    schema = (Path(__file__).resolve().parents[1] / "sql/schema.sql").read_text()
    try:
        with conn.transaction():
            conn.execute(schema)
            for title, desc, genres, platforms, price in GAMES:
                text = f"{title}. {desc}. Genres: {', '.join(genres)}. Platforms: {', '.join(platforms)}."
                conn.execute("INSERT INTO games(title,description,genres,platforms,pricing_model,embedding) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT(title) DO UPDATE SET description=EXCLUDED.description,genres=EXCLUDED.genres,platforms=EXCLUDED.platforms,pricing_model=EXCLUDED.pricing_model,embedding=EXCLUDED.embedding",
                             (title,desc,genres,platforms,price,embed(text)))
            conn.execute("INSERT INTO users(username) VALUES ('DemoPlayer'),('DemoFriend') ON CONFLICT(username) DO NOTHING")
            conn.execute("INSERT INTO demo_wallets(user_id,credits) SELECT id,100 FROM users WHERE username IN ('DemoPlayer','DemoFriend') ON CONFLICT(user_id) DO NOTHING")
            for title, *_ in GAMES:
                gid = conn.execute("SELECT id FROM games WHERE title=%s",(title,)).fetchone()["id"]
                if not conn.execute("SELECT 1 FROM reviews WHERE game_id=%s AND is_fictional=TRUE LIMIT 1",(gid,)).fetchone():
                    for name,rating,body in REVIEWS[:2]:
                        conn.execute("INSERT INTO reviews(game_id,username,rating,body,is_fictional) VALUES (%s,%s,%s,%s,TRUE)",(gid,name,rating,body))
        print(f"Initialized {len(GAMES)} games and fictional reviews.")
    finally: conn.close()

if __name__ == "__main__": main()
