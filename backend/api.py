import logging

from fastapi import FastAPI, HTTPException

from backend.service import list_games

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Steamish API",
    description="HTTP API for the Steamish gaming catalogue.",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/games")
def get_games():
    try:
        games = list_games()
        return {"items": games, "count": len(games)}
    except Exception as exc:
        logger.exception("Failed to retrieve games")
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve games.",
        ) from exc
