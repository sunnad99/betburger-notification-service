import os
import json
from dotenv import load_dotenv

load_dotenv()


CONFIG_FILENAME = os.environ.get("CONFIG_FILENAME", "bot_test_config.json")

# Load the credentials from the config file
CREDS = {}
with open(CONFIG_FILENAME, "r") as f:
    CREDS = json.load(f)

# Load the credentials for telegram
TELEGRAM_AUTH_TOKEN = CREDS.get("TELEGRAM_AUTH_TOKEN")
TELEGRAM_CHAT_MAPPING = CREDS.get("TELEGRAM_CHAT_MAPPING", {})

# Load the credentials for betburger
BET_BURGER_TOKEN = CREDS.get("BET_BURGER_TOKEN")
BET_BURGER_FILTER_ID = CREDS.get("BET_BURGER_FILTER_ID")

# Load the credentials for stripe
STRIPE_AUTH_TOKEN = os.getenv("STRIPE_AUTH_TOKEN")
STRIPE_PUBLISHABLE_TOKEN = os.getenv("STRIPE_PUBLISHABLE_TOKEN")

# Load credentials for ngrok
NGROK_AUTH_TOKEN = os.getenv("NGROK_AUTH_TOKEN")

# Other creds
STATIC_DIR = os.getenv("STATIC_DIR", "./")
