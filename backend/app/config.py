import os
from pathlib import Path

# Resolve base directories safely
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent if (BACKEND_DIR.parent / "data").exists() else BACKEND_DIR

DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
PREDICTIONS_DIR = PROJECT_ROOT / "predictions"
DB_PATH = Path(os.getenv("FAIRGIG_DB_PATH", BACKEND_DIR / "app" / "fairgig.db"))

# Default hyperparameters
DEFAULT_LAMBDA = 0.08
ENSEMBLE_THRESHOLD = 0.155

# Ensure app directories exist
(BACKEND_DIR / "app").mkdir(exist_ok=True)
