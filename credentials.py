import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
BET_BURGER_TOKEN = os.environ.get("BET_BURGER_TOKEN")
BET_BURGER_FILTER_ID = os.environ.get("BET_BURGER_FILTER_ID")
