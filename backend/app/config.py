import os
from dotenv import load_dotenv
load_dotenv()
APP_NAME = os.getenv("APP_NAME", "EARTH AI")
MODE = os.getenv("EARTH_AI_MODE", "api").lower()
BASE_URL = os.getenv("MODEL_BASE_URL", "").rstrip("/")
API_KEY = os.getenv("MODEL_API_KEY", "")
MODEL = os.getenv("MODEL_NAME", "earth-model")
TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.getenv("MODEL_MAX_TOKENS", "2048"))
DB_PATH = os.getenv("DATABASE_PATH", "./earth_ai.db")
ORIGINS = [x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip()]
