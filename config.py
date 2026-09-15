import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = []
MAX_FILE_SIZE_MB = 50
MAX_DURATION_MIN = 60
MAX_CONCURRENT_DOWNLOADS = 3
RATE_LIMIT_PER_HOUR = 20
DOWNLOAD_DIR = "./downloads"
COOKIES_FILE = "cookies.txt"
