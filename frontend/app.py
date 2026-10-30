import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st
from backend.client import request

st.set_page_config(page_title="Steamish | Discover games", page_icon="🎮", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: radial-gradient(ellipse at 15% 0%, #172b3d 0, #0b1118 38%, #0a0e13 100%); }
.block-container { max-width: 1500px; padding-top: 1.5rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] { background: #0d151e; border-right: 1px solid #263545; }
.hero { padding: 1.6rem 1.8rem; border: 1px solid #2c4052; border-radius: 18px; background: linear-gradient(120deg, rgba(31,77,105,.72), rgba(20,31,44,.92) 60%, rgba(28,45,54,.72)); margin-bottom: 1.25rem; }
.eyebrow { color: #8fd4ff; font-size: .76rem; letter-spacing: .16em; font-weight: 800; text-transform: uppercase; }
.hero h1 { margin: .35rem 0 .25rem; font-size: 2.35rem; letter-spacing: -.04em; }
.hero p { color: #bdcad6; margin-bottom: 0; }
.game-card { border: 1px solid #263747; border-radius: 15px; padding: 1rem; background: linear-gradient(160deg, rgba(24,37,50,.96), rgba(14,21,30,.96)); min-height: 220px; }
.game-card h3 { margin: .25rem 0 .6rem; font-size: 1.12rem; }
.muted { color: #9aabba; font-size: .88rem; }
.pill { display: inline-block; background: #1d3445; border: 1px solid #34546a; color: #bfe7ff; border-radius: 999px; padding: .18rem .55rem; font-size: .72rem; margin: .1rem .18rem .1rem 0; }
.metric { background: #111d28; border: 1px solid #263747; border-radius: 12px; padding: .8rem 1rem; }
.metric strong { font-size: 1.35rem; color: #eaf6ff; }
div.stButton > button { border-radius: 9px; font-weight: 650; }
.stTabs [data-baseweb="tab-list"] { gap: .45rem; }
.stTabs [data-baseweb="tab"] { border-radius: 9px 9px 0 0; padding: .7rem 1rem; }
</style>
<div class="hero"><div class="eyebrow">Your next favourite game</div><h1>Discover something worth playing.</h1><p>Explore the catalogue, read community reviews, and find your next adventure with vector-powered recommendations.</p></div>
""", unsafe_allow_html=True)

if "selected_game_id" not in st.session_state:
    st.session_state.selected_game_id = None
if "last_recommendations" not in st.session_state:
    st.session_state.last_recommendations = []


def call(payload):
    try:
        result = request(payload)
        if isinstance(result, dict) and result.get("error"):
            st.error(result["error"])
            return None
        return result
    except Exception as exc:
        st.error(f"Couldn't reach the backend ({type(exc).__name__}: {exc}). Check that `python -m backend.server` is running in another terminal.")
        return None


def game_card(game, key_prefix="game"):
    with st.container(border=True):
        st.markdown(f"### {game['title']}")
        st.markdown(f"<div class='muted'>{game.get('pricing_model', 'Pricing varies')} · {', '.join(game.get('platforms') or [])}</div>", unsafe_allow_html=True)
        st.write(game.get("description", "No description available."))
        genres = game.get("genres") or []
        if genres:
            st.markdown("".join(f"<span class='pill'>{genre}</span>" for genre in genres[:5]), unsafe_allow_html=True)
        if st.button("View details", key=f"{key_prefix}_{game['id']}", use_container_width=True):
            st.session_state.selected_game_id = int(game["id"])
            st.toast(f"Selected {game['title']}. Open the Game details tab.")
            st.rerun()

with st.sidebar:
    st.markdown("## 🎮 Steamish")
    st.caption("Game discovery · metadata only")
    st.markdown("---")
    st.markdown("**Quick tips**")
    st.caption("• Choose **View details** on any game, then open Game details.\n\n• Recommendations work from a game or a description of your taste.\n\n• Demo reviews are labelled fictional.")
    st.markdown("---")
    if st.button("Clear selected game", use_container_width=True):
        st.session_state.selected_game_id = None
        st.rerun()

browse, details_tab, recs, library, acid = st.tabs(["🔎 Discover", "📖 Game details", "✨ Recommendations", "📚 My library", "⚙️ Transaction demo"])

with browse:
    filters = st.container()
    with filters:
        qcol, gcol, pcol = st.columns([2.2, 1, 1])
        query = qcol.text_input("Search games", placeholder="Try Elden Ring, space exploration, farming…")
        genre_options = ["Any"] + sorted(["Action", "Adventure", "Automation", "Battle Royale", "Co-op", "Competitive", "Deckbuilder", "Horror", "Indie", "MMORPG", "Open World", "Platformer", "Puzzle", "Racing", "RPG", "Roguelike", "Sandbox", "Simulation", "Strategy", "Survival", "FPS"])
        genre = gcol.selectbox("Genre", genre_options)
        platform = pcol.selectbox("Platform", ["Any", "PC", "PlayStation", "Xbox", "Switch", "Mobile"])
    f = {}
    if query.strip(): f["query"] = query.strip()
    if genre != "Any": f["genre"] = genre
    if platform != "Any": f["platform"] = platform
    result = call({"action": "list_games", "filters": f})
    if result is not None:
        games = result.get("games", [])
        m1, m2, m3 = st.columns(3)
        with m1: st.markdown(f"<div class='metric'><strong>{len(games)}</strong><br><span class='muted'>Games in these results</span></div>", unsafe_allow_html=True)
        with m2: st.markdown("<div class='metric'><strong>Vector search</strong><br><span class='muted'>Content-based discovery</span></div>", unsafe_allow_html=True)
        with m3: st.markdown(f"<div class='metric'><strong>{'Cache hit' if result.get('cached') else 'Live query'}</strong><br><span class='muted'>Catalogue source</span></div>", unsafe_allow_html=True)
        st.write("")
        if not games:
            st.info("No games matched those filters. Try a broader search.")
        else:
            cols = st.columns(3, gap="medium")
            for i, game in enumerate(games):
                with cols[i % 3]: game_card(game, "browse")

with details_tab:
    gid = st.session_state.selected_game_id
    if gid is None:
        st.info("Choose **View details** on a game in Discover to see its full page here.")
    else:
        d = call({"action": "game_details", "game_id": gid})
        if d and not d.get("error"):
            st.markdown(f"<div class='eyebrow'>Game profile</div><h1>{d['title']}</h1>", unsafe_allow_html=True)
            st.markdown("".join(f"<span class='pill'>{x}</span>" for x in (d.get("genres") or [])), unsafe_allow_html=True)
            st.write("")
            a, b = st.columns([2, 1])
            with a:
                st.subheader("About this game")
                st.write(d.get("description", "No description available."))
            with b:
                st.markdown(f"<div class='metric'><strong>{d.get('pricing_model', 'Unknown')}</strong><br><span class='muted'>Pricing model</span><br><br><strong>{len(d.get('reviews', []))}</strong><br><span class='muted'>Recent reviews shown</span></div>", unsafe_allow_html=True)
                st.write("**Platforms**")
                st.write(", ".join(d.get("platforms") or []) or "Not listed")
                if st.button("＋ Add to my library", key=f"add_detail_{gid}", use_container_width=True):
                    x = call({"action": "add_to_library", "username": "DemoPlayer", "game_id": gid})
                    if x and x.get("ok"): st.success(x.get("message", "Added."))
            st.markdown("---")
            st.subheader("Community reviews")
            reviews = d.get("reviews") or []
            if not reviews: st.caption("No reviews yet. Be the first to leave one.")
            for review in reviews:
                label = "Fictional demo" if review.get("is_fictional") else "Community review"
                with st.container(border=True):
                    st.markdown(f"**{review.get('username', 'Player')}** &nbsp; · &nbsp; {'⭐' * int(review.get('rating', 0))} &nbsp; <span class='muted'>{label}</span>", unsafe_allow_html=True)
                    st.write(review.get("body", ""))
                    if review.get("created_at"): st.caption(str(review["created_at"])[:10])
            with st.form(f"review_form_{gid}", clear_on_submit=True):
                st.markdown("#### Write a review")
                name = st.text_input("Display name", value="Player", max_chars=40)
                rating = st.select_slider("Your rating", options=[1, 2, 3, 4, 5], value=4, format_func=lambda x: f"{x} / 5")
                body = st.text_area("Your review", placeholder="What did you enjoy? What should other players know?", max_chars=1000, help="Please write between 5 and 1000 characters.")
                submitted = st.form_submit_button("Publish review", type="primary", use_container_width=True)
                if submitted:
                    x = call({"action": "add_review", "game_id": gid, "username": name, "rating": rating, "body": body})
                    if x and x.get("ok"):
                        st.success(x.get("message", "Review saved."))
                        st.rerun()

with recs:
    st.subheader("Find your next favourite")
    st.write("Recommendations compare game-description embeddings stored in PostgreSQL with pgvector.")
    mode = st.radio("Recommend based on", ["A game I like", "Describe my taste"], horizontal=True)
    if mode == "A game I like":
        x = call({"action": "list_games", "filters": {}})
        if x:
            opts = {g["title"]: g["id"] for g in x.get("games", [])}
            if opts:
                titles = list(opts)
                default_idx = next((i for i, title in enumerate(titles) if st.session_state.selected_game_id and opts[title] == st.session_state.selected_game_id), 0)
                chosen = st.selectbox("Choose a reference game", titles, index=default_idx)
                if st.button("✨ Find similar games", type="primary"):
                    y = call({"action": "recommendations", "game_id": opts[chosen], "limit": 8})
                    st.session_state.last_recommendations = y.get("games", []) if y else []
                    st.session_state.recommendation_source = chosen
            else: st.warning("No games are available to recommend yet.")
    else:
        taste = st.text_area("What do you enjoy playing?", placeholder="Exploration, co-op, crafting, challenging combat, and a strong story…", height=110)
        if st.button("✨ Recommend for me", type="primary", disabled=not taste.strip()):
            y = call({"action": "recommendations", "query": taste, "limit": 10})
            st.session_state.last_recommendations = y.get("games", []) if y else []
            st.session_state.recommendation_source = "your description"
    recommendations = st.session_state.get("last_recommendations", [])
    if recommendations:
        st.markdown(f"### Picks based on {st.session_state.get('recommendation_source', 'your taste')}")
        cols = st.columns(2, gap="medium")
        for i, game in enumerate(recommendations):
            with cols[i % 2]:
                with st.container(border=True):
                    sim = game.get("similarity")
                    st.markdown(f"### {game['title']}")
                    if sim is not None: st.progress(max(0.0, min(1.0, float(sim))), text=f"Vector similarity · {float(sim):.0%}")
                    st.write(game.get("description", ""))
                    st.caption(" · ".join(game.get("genres") or []))
                    if st.button("Open game details", key=f"rec_detail_{game['id']}"):
                        st.session_state.selected_game_id = int(game["id"])
                        st.toast("Open the Game details tab to view this game.")
                        st.rerun()
    elif st.session_state.get("recommendation_source"):
        st.info("No recommendations were returned. Check the backend terminal for the database error.")

with library:
    st.subheader("Your demo library")
    st.caption("Games are saved to PostgreSQL under the demo user DemoPlayer.")
    x = call({"action": "list_library", "username": "DemoPlayer"})
    if x:
        saved = x.get("games", [])
        if not saved: st.info("Your library is empty. Open a game's details and choose Add to my library.")
        else:
            cols = st.columns(3)
            for i, game in enumerate(saved):
                with cols[i % 3]: game_card(game, "library")

with acid:
    st.subheader("Atomic transaction demo")
    st.warning("Fictional demo credits only — not money or purchases.")
    x = call({"action": "get_wallets"})
    if x:
        cols = st.columns(2)
        for i, wallet in enumerate(x.get("wallets", [])):
            with cols[i % 2]: st.markdown(f"<div class='metric'><strong>{wallet['credits']} credits</strong><br><span class='muted'>{wallet['username']}</span></div>", unsafe_allow_html=True)
    with st.form("transfer_form"):
        src = st.selectbox("Transfer from", ["DemoPlayer", "DemoFriend"])
        dst = "DemoFriend" if src == "DemoPlayer" else "DemoPlayer"
        st.write(f"Transfer to **{dst}**")
        amount = st.number_input("Credits", min_value=1, max_value=100, value=10)
        if st.form_submit_button("Transfer atomically", type="primary"):
            y = call({"action": "transfer_demo_credits", "from_username": src, "to_username": dst, "amount": amount})
            if y and y.get("ok"):
                st.success(y.get("message", "Transfer complete."))
                st.rerun()

st.markdown("---")
st.caption("Steamish is a learning project. It stores game metadata and demo reviews, not game files. Seed reviews are fictional examples.")
