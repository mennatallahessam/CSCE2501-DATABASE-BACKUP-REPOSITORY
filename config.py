import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env (or .env.example if .env missing)
_env_path = Path(__file__).parent / '.env'
if not _env_path.is_file():
    _env_path = Path(__file__).parent / '.env.example'
load_dotenv(_env_path)

# Configuration constants
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '3306'))
DB_NAME = os.getenv('DB_NAME', 'resale_db')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

# Crawler settings
RATE_LIMIT_SECONDS = float(os.getenv('RATE_LIMIT_SECONDS', '3'))  # base delay
JITTER_SECONDS = float(os.getenv('JITTER_SECONDS', '1'))        # +/- jitter
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '5'))

# Faker seed for reproducibility
FAKER_SEED = int(os.getenv('FAKER_SEED', '12345'))

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
RAW_DIR = PROJECT_ROOT / 'raw'
SAMPLES_DIR = PROJECT_ROOT / 'samples'
OUTPUT_DIR = PROJECT_ROOT / 'output'
STATE_FILE = PROJECT_ROOT / 'crawler_state.jsonl'

# Ensure directories exist
for _p in [RAW_DIR, SAMPLES_DIR, OUTPUT_DIR]:
    _p.mkdir(parents=True, exist_ok=True)

