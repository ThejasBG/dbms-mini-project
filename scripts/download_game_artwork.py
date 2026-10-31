r"""
Automatically download and validate Steamish catalogue artwork.

Run from the repository root:
    .\.venv\Scripts\python.exe scripts\download_game_artwork.py

The script preserves existing landscape artwork, detects unsuitable portrait/square
covers, tries verified Steam header art, then Wikipedia and Wikimedia Commons
landscape images. If no suitable image is found, the frontend CSS fallback is used.
"""
from __future__ import annotations

import json
import re
import struct
import time
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "web" / "public" / "images" / "games"
MANIFEST_PATH = IMAGE_DIR / "manifest.json"
MIN_BYTES = 1500
MIN_WIDTH = 300
MIN_HEIGHT = 120
MIN_ASPECT_RATIO = 1.4

GAMES = [
    "Counter-Strike 2", "Dota 2", "PUBG: Battlegrounds", "Apex Legends",
    "Fortnite", "Minecraft", "Grand Theft Auto V", "Red Dead Redemption 2",
    "Elden Ring", "Baldur's Gate 3", "The Witcher 3: Wild Hunt", "Cyberpunk 2077",
    "Stardew Valley", "Terraria", "Hades", "Hollow Knight", "Celeste", "Among Us",
    "Rocket League", "Overwatch 2", "Rainbow Six Siege", "Warframe",
    "Final Fantasy XIV", "World of Warcraft", "The Sims 4", "Cities: Skylines",
    "Civilization VI", "Age of Empires II: Definitive Edition", "Path of Exile",
    "League of Legends", "Dead by Daylight", "Phasmophobia", "Subnautica",
    "No Man's Sky", "Sea of Thieves", "Forza Horizon 5", "Need for Speed Heat",
    "Euro Truck Simulator 2", "Factorio", "Satisfactory", "Portal 2", "God of War",
    "Marvel's Spider-Man Remastered", "Persona 5 Royal", "Undertale", "Slay the Spire",
    "Balatro", "Dave the Diver", "Helldivers 2", "Black Myth: Wukong",
    "Hogwarts Legacy", "Fall Guys", "The Finals",
]

ALIASES = {
    "PUBG: Battlegrounds": ["PUBG Battlegrounds", "PUBG: BATTLEGROUNDS"],
    "Grand Theft Auto V": ["Grand Theft Auto V", "Grand Theft Auto V Enhanced", "GTA V"],
    "The Witcher 3: Wild Hunt": ["The Witcher 3 Wild Hunt", "The Witcher 3"],
    "Rocket League": ["Rocket League"],
    "Rainbow Six Siege": ["Tom Clancy's Rainbow Six Siege", "Rainbow Six Siege X", "Rainbow Six Siege"],
    "Final Fantasy XIV": ["FINAL FANTASY XIV Online", "Final Fantasy XIV Online", "Final Fantasy XIV"],
    "Civilization VI": ["Sid Meier's Civilization VI", "Civilization VI"],
    "Sea of Thieves": ["Sea of Thieves"],
    "Fall Guys": ["Fall Guys", "Fall Guys: Ultimate Knockout"],
    "The Finals": ["THE FINALS"],
    "Baldur's Gate 3": ["Baldur's Gate 3"],
    "No Man's Sky": ["No Man's Sky"],
}

KNOWN_APP_IDS = {
    "Grand Theft Auto V": 271590,
    "The Witcher 3: Wild Hunt": 292030,
    "Rocket League": 252950,
    "Rainbow Six Siege": 359550,
    "Final Fantasy XIV": 39210,
    "Civilization VI": 289070,
    "Sea of Thieves": 1172620,
    "Fall Guys": 1097150,
    "Overwatch 2": 2357570,
}

WIKIPEDIA_TITLES = {
    "Fortnite": "Fortnite",
    "Minecraft": "Minecraft",
    "World of Warcraft": "World of Warcraft",
    "League of Legends": "League of Legends",
}


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold().replace("&", "and"))


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def get_json(session: requests.Session, url: str, *, params: dict | None = None) -> dict:
    response = session.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def steam_name_matches(title: str, returned_name: str, aliases: list[str]) -> bool:
    actual = normalize(returned_name)
    accepted = {normalize(title), *(normalize(alias) for alias in aliases)}
    return actual in accepted


def image_dimensions(data: bytes) -> tuple[int, int] | None:
    """Read common image dimensions using only the Python standard library."""
    # PNG
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    # GIF
    if data[:6] in (b"GIF87a", b"GIF89a") and len(data) >= 10:
        return struct.unpack("<HH", data[6:10])
    # WebP (VP8X)
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP" and len(data) >= 30:
        if data[12:16] == b"VP8X":
            width = 1 + int.from_bytes(data[24:27], "little")
            height = 1 + int.from_bytes(data[27:30], "little")
            return width, height
    # JPEG
    if data.startswith(b"\xff\xd8"):
        i = 2
        while i + 4 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            while i < len(data) and data[i] == 0xFF:
                i += 1
            if i >= len(data):
                break
            marker = data[i]
            i += 1
            if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                continue
            if i + 2 > len(data):
                break
            segment_length = int.from_bytes(data[i:i + 2], "big")
            if segment_length < 2 or i + segment_length > len(data):
                break
            if marker in (
                0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
            ):
                if segment_length >= 7:
                    height = int.from_bytes(data[i + 3:i + 5], "big")
                    width = int.from_bytes(data[i + 5:i + 7], "big")
                    return width, height
                break
            i += segment_length
    return None


def valid_landscape(data: bytes) -> tuple[bool, str]:
    if len(data) < MIN_BYTES:
        return False, "file is too small"
    dimensions = image_dimensions(data)
    if not dimensions:
        return False, "image dimensions could not be read"
    width, height = dimensions
    if width < MIN_WIDTH or height < MIN_HEIGHT:
        return False, f"image is too small ({width}x{height})"
    ratio = width / height
    if ratio < MIN_ASPECT_RATIO:
        return False, f"not landscape enough ({width}x{height}, ratio {ratio:.2f})"
    return True, f"{width}x{height}"


def fetch_image(session: requests.Session, url: str) -> bytes | None:
    try:
        response = session.get(url, timeout=25)
        response.raise_for_status()
        if "image" not in response.headers.get("content-type", "").lower():
            return None
        valid, reason = valid_landscape(response.content)
        if not valid:
            print(f"    Rejected image: {reason}")
            return None
        return response.content
    except (requests.RequestException, OSError):
        return None


def find_steam_image(session: requests.Session, title: str) -> dict | None:
    aliases = ALIASES.get(title, [title])
    for term in aliases:
        search_url = "https://store.steampowered.com/api/storesearch/"
        try:
            results = get_json(
                session, search_url,
                params={"term": term, "l": "english", "cc": "us"},
            ).get("items", [])
        except (requests.RequestException, ValueError):
            continue
        matches = [
            item for item in results
            if item.get("id") and steam_name_matches(title, item.get("name", ""), aliases)
        ]
        if matches:
            item = matches[0]
            return {"app_id": int(item["id"]), "store_name": item.get("name", "")}
        time.sleep(0.15)

    app_id = KNOWN_APP_IDS.get(title)
    if app_id:
        try:
            data = get_json(
                session,
                f"https://store.steampowered.com/api/appdetails/?appids={app_id}&l=english",
            )
            record = data.get(str(app_id), {})
            details = record.get("data", {})
            if record.get("success") and steam_name_matches(
                title, details.get("name", ""), aliases
            ):
                return {"app_id": app_id, "store_name": details.get("name", "")}
        except (requests.RequestException, ValueError):
            pass
    return None


def find_wikipedia_image(session: requests.Session, title: str) -> dict | None:
    page_title = WIKIPEDIA_TITLES.get(title, title)
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(
        page_title.replace(" ", "_")
    )
    try:
        data = get_json(session, url)
        image = data.get("originalimage") or data.get("thumbnail")
        if image and image.get("source"):
            return {
                "url": image["source"],
                "page_title": data.get("title", page_title),
                "source": "Wikipedia page image",
            }
    except (requests.RequestException, ValueError):
        pass
    return None


def find_commons_landscape(session: requests.Session, title: str) -> dict | None:
    """Search Wikimedia Commons and accept only a relevant, sufficiently wide image."""
    query_title = title
    search_terms = [f'"{query_title}" landscape', f'"{query_title}" game artwork']
    # Common short name for this game, useful when its full title returns poor matches.
    if title == "World of Warcraft":
        search_terms = ['"World of Warcraft" landscape', '"World of Warcraft" game scenery']
    for term in search_terms:
        try:
            data = get_json(
                session,
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "search",
                    "gsrsearch": term,
                    "gsrnamespace": 6,
                    "gsrlimit": 12,
                    "prop": "imageinfo",
                    "iiprop": "url|size",
                    "format": "json",
                },
            )
        except (requests.RequestException, ValueError):
            continue

        pages = (data.get("query") or {}).get("pages") or {}
        candidates = []
        title_tokens = [
            token for token in re.findall(r"[a-z0-9]+", title.casefold())
            if len(token) > 2 and token not in {"the", "edition", "online"}
        ]
        for page in pages.values():
            page_name = page.get("title", "")
            info_list = page.get("imageinfo") or []
            if not info_list:
                continue
            info = info_list[0]
            width, height = info.get("width", 0), info.get("height", 0)
            if not width or not height or width / height < MIN_ASPECT_RATIO:
                continue
            normalized_name = normalize(page_name)
            # Require a meaningful title overlap to avoid unrelated landscape images.
            overlap = sum(1 for token in title_tokens if normalize(token) in normalized_name)
            if not overlap:
                continue
            url = info.get("url")
            if url:
                candidates.append((overlap, width, url, page_name))
        candidates.sort(reverse=True)
        for _, _, url, page_name in candidates:
            data_bytes = fetch_image(session, url)
            if data_bytes:
                return {
                    "url": url,
                    "page_title": page_name,
                    "source": "Wikimedia Commons landscape image",
                    "bytes": data_bytes,
                }
    return None


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({
        "User-Agent": "SteamishArtworkDownloader/1.1 (student catalogue project)"
    })

    try:
        old_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if not isinstance(old_manifest, dict):
            old_manifest = {}
    except (OSError, json.JSONDecodeError):
        old_manifest = {}

    manifest = dict(old_manifest)
    success_count = 0
    redownload_count = 0
    fallback_count = 0
    failed = []

    for index, title in enumerate(GAMES, start=1):
        filename = f"{slugify(title)}.jpg"
        destination = IMAGE_DIR / filename
        existing = manifest.get(title, {})
        existing_bytes = destination.read_bytes() if destination.exists() else b""
        if existing_bytes:
            valid, reason = valid_landscape(existing_bytes)
            if valid:
                manifest[title] = {**existing, "local": f"/images/games/{filename}"}
                success_count += 1
                print(f"[{index:02}/{len(GAMES)}] Keeping landscape cover: {title} ({reason})")
                continue
            print(f"[{index:02}/{len(GAMES)}] Replacing unsuitable cover: {title} ({reason})")
            redownload_count += 1
        else:
            print(f"[{index:02}/{len(GAMES)}] Finding artwork: {title}")

        image_bytes = None
        image_metadata = None

        steam = find_steam_image(session, title)
        if steam:
            app_id = steam["app_id"]
            image_url = (
                "https://shared.akamai.steamstatic.com/store_item_assets/"
                f"steam/apps/{app_id}/header.jpg"
            )
            image_bytes = fetch_image(session, image_url)
            if image_bytes:
                image_metadata = {
                    "appId": app_id,
                    "external": image_url,
                    "source": "Steam Store artwork",
                    "storeName": steam["store_name"],
                }
                print(f"    Selected Steam landscape artwork: {steam['store_name']}")

        if image_bytes is None:
            wiki = find_wikipedia_image(session, title)
            if wiki:
                candidate_bytes = fetch_image(session, wiki["url"])
                if candidate_bytes:
                    image_bytes = candidate_bytes
                    image_metadata = {
                        "external": wiki["url"],
                        "source": wiki["source"],
                        "sourcePage": wiki["page_title"],
                    }
                    fallback_count += 1
                    print(f"    Selected Wikipedia landscape image: {wiki['page_title']}")

        if image_bytes is None:
            commons = find_commons_landscape(session, title)
            if commons:
                image_bytes = commons["bytes"]
                image_metadata = {
                    "external": commons["url"],
                    "source": commons["source"],
                    "sourcePage": commons["page_title"],
                }
                fallback_count += 1
                print(f"    Selected Commons landscape image: {commons['page_title']}")

        if image_bytes is not None and image_metadata is not None:
            destination.write_bytes(image_bytes)
            manifest[title] = {
                **image_metadata,
                "local": f"/images/games/{filename}",
            }
            success_count += 1
            time.sleep(0.15)
        else:
            # Remove the stale manifest entry so the frontend uses its CSS fallback,
            # rather than continuing to show the unsuitable portrait image.
            manifest.pop(title, None)
            if destination.exists():
                destination.unlink()
            failed.append(title)
            print("    No suitable landscape image found; CSS fallback will be used.")

    MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("\nArtwork summary")
    print(f"Suitable local landscape covers: {success_count}/{len(GAMES)}")
    print(f"Replaced unsuitable existing covers: {redownload_count}")
    print(f"Landscape covers from secondary sources: {fallback_count}")
    print(f"Using CSS fallback: {len(failed)}")
    for title in failed:
        print(f"  - {title}")
    print(f"Manifest updated: {MANIFEST_PATH}")
    print("Review the catalogue before committing.")


if __name__ == "__main__":
    main()
