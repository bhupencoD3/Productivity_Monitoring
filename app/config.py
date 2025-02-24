# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file if used

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "prod_user"),
    "password": os.getenv("DB_PASSWORD", "room"),
    "database": os.getenv("DB_NAME", "productivity_db"),
}

