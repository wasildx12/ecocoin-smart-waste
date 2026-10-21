"""Central configuration for EcoCoin."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DATABASE_PATH = DATA_DIR / "ecocoin.db"

APP_NAME = "EcoCoin"
APP_TAGLINE = "Small actions. Greener communities."
DEFAULT_REWARD_RATES = {
    "Plastic": 10,
    "Polythene": 8,
    "Rubber": 6,
    "Wood": 4,
}
REJECTED_CATEGORIES = {"Automobile waste", "Construction waste"}
