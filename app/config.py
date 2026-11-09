import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
if not GROQ_API_KEY:
    raise ValueError(f"Переменная GROQ_API_KEY не найдена в .env по пути: {BASE_DIR / '.env'}")

# Используемая модель Groq API
MODEL_NAME = "qwen/qwen3.8-27b"