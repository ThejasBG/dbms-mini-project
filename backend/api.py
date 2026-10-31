import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.service import list_games

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Steamish API",
    description="HTTP API for the Steamish gaming catalogue.",
    version="1.0.0",
)

# Allow the local Next.js development server to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/games")
def get_games():
    try:
        result = list_games()
        games = result.get("games", [])

        return {
            "items": games,
            "count": len(games),
            "cached": result.get("cached", False),
        }
    except Exception as exc:
        logger.exception("Failed to retrieve games")
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve games.",
        ) from exc