import os
from dotenv import load_dotenv

# Configuration comes from the environment or a project-root .env file.
# No database credential is embedded in the source code.
load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} is not set. Copy .env.example to .env and set {name} "
            "(see the README setup instructions)."
        )
    return value


DATABASE_URL = _required("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TCP_HOST = os.getenv("TCP_HOST", "127.0.0.1")
TCP_PORT = int(os.getenv("TCP_PORT", "8765"))
