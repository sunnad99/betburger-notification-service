import time
from config import BASE_MESSAGE, TIME_ZONE
from credentials import (
    BET_BURGER_TOKEN,
    BET_BURGER_FILTER_ID,
    TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID,
)
from utils import process_bets, format_messages, send_message, load_duplicate_records
from database import Database

# Initialize the database
db = Database()

# Obtain the bets from BetBurger
bets = process_bets(BET_BURGER_TOKEN, BET_BURGER_FILTER_ID)

# Check if there are any bets retrieved from the API
if not bets.empty:

    # Retrieve duplicate records, if they exist, from the database
    new_bets = load_duplicate_records(bets, db)

    # Only if there are new bets, insert them into the database and send the messages to the Telegram channel
    if new_bets:

        # Insert the new bets into the database
        db.insert_data(new_bets)

        # Format the bets into messages
        messages = format_messages(bets, BASE_MESSAGE, TIME_ZONE)

        # Send the messages to the Telegram channel
        for message in messages:
            send_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message)
            time.sleep(3)
