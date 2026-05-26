from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR / 'geo_brand_search.db'}"

SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
