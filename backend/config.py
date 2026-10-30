import os
from dotenv import load_dotenv

# Values in a project-root .env override these local-development defaults.
load_dotenv()
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:Zoro@localhost:5432/game_catalog",
)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TCP_HOST = os.getenv("TCP_HOST", "127.0.0.1")
TCP_PORT = int(os.getenv("TCP_PORT", "8765"))
