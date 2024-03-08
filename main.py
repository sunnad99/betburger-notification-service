import time
from config import BASE_MESSAGE, TIME_ZONE
from credentials import (
    BET_BURGER_TOKEN,
    BET_BURGER_FILTER_ID,
    TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID,
)
from utils import process_bets, format_messages, send_message
from database import Database

# Initialize the database
db = Database()

# Obtain the bets from BetBurger
bets = process_bets(BET_BURGER_TOKEN, BET_BURGER_FILTER_ID)

# Check if there are any bets to send
if not bets.empty:

    # Store the bets in the database

    # Format the bets into messages
    messages = format_messages(bets, BASE_MESSAGE, TIME_ZONE)

    print(messages)

    # # Send the messages to the Telegram channel
    # for message in messages:
    #     send_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message)
    #     time.sleep(3)
