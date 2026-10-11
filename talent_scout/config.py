import os
from pathlib import Path

from dotenv import load_dotenv

# Directory containing this file (talent_scout/). All default paths are
# resolved relative to it so the app works regardless of the current
# working directory.
BASE_DIR = Path(__file__).resolve().parent

# Searches for a .env file starting from this directory and walking upwards.
load_dotenv()

DATA_DIR = os.path.realpath(
    os.getenv("TALENT_SCOUT_DATA_DIR", str(BASE_DIR / "data" / "jobs"))
)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

MAX_UPLOAD_MB = float(os.getenv("TALENT_SCOUT_MAX_UPLOAD_MB", "10"))
MAX_UPLOAD_BYTES = int(MAX_UPLOAD_MB * 1024 * 1024)

# Maximum number of PDF pages converted and OCR'd per document.
MAX_PDF_PAGES = int(os.getenv("TALENT_SCOUT_MAX_PDF_PAGES", "10"))
