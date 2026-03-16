import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "sales.db")
DEFAULT_TABLE = "sales"
