import os
import certifi
from dotenv import load_dotenv

# Fix SSL certificate issue in conda environments on Windows
os.environ["SSL_CERT_FILE"] = certifi.where()

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
