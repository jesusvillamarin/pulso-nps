from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "pulso.db"
EXAMPLE_PATH = Path(__file__).resolve().parent / "assets" / "nps_ejemplo.csv"

MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_ROWS = 10_000
PREVIEW_ROWS = 20
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
BATCH_SIZE = max(1, min(int(os.getenv("TYPESAFE_BATCH_SIZE", "10")), 25))
TYPESAFE_MOCK = os.getenv("TYPESAFE_MOCK", "0") == "1"
