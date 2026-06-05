import os

from dotenv import load_dotenv

from utils import get_base_dir

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
PHONE = os.getenv("PHONE", "")

CHANNEL_ID = os.getenv("CHANNEL_ID", "")
STATUS_CHAT_ID = os.getenv("STATUS_CHAT_ID", "me")

SESSION_NAME = str(get_base_dir() / os.getenv("SESSION_NAME", "gifts_checker"))

STICKERSET_TITLE = os.getenv("STICKERSET_TITLE", "Telegram Gifts")
STICKERSET_SHORT_NAME = os.getenv("STICKERSET_SHORT_NAME", "")

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))
STATUS_INTERVAL = int(os.getenv("STATUS_INTERVAL", "3600"))
