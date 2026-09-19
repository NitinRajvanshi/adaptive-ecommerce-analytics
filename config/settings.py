from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Main directories
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"
LOG_DIR = BASE_DIR / "logs"
EXPORT_DIR = BASE_DIR / "exports"

# Database
DATABASE_PATH = DATABASE_DIR / "ecommerce_analytics.db"

# Application
APP_NAME = "Adaptive E-Commerce Analytics & ETL Intelligence Platform"

# Upload limits
MAX_UPLOAD_SIZE_MB = 50

# Supported file types
SUPPORTED_FILE_TYPES = [".csv"]