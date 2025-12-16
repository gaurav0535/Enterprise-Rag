from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

STORAGE_DIR = BASE_DIR / "storage"

STORAGE_DIR.mkdir(exist_ok = True)


