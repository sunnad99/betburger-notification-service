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
import time
import logging
from config import BASE_MESSAGE, TIME_ZONE
from utils import process_bets, format_messages, send_message, load_duplicate_records
from database import Database

from credentials import (
    BET_BURGER_TOKEN,
    BET_BURGER_FILTER_ID,
    TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID,
)

# Initialize the logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Initialize the database
db = Database()
logging.info("Database initialized")

# Obtain the bets from BetBurger
bets = process_bets(BET_BURGER_TOKEN, BET_BURGER_FILTER_ID)

# Check if there are any bets retrieved from the API
if not bets.empty:
    logging.info(f"{len(bets)} Bets retrieved from the API")

    # Retrieve duplicate records, if they exist, from the database
    new_bets = load_duplicate_records(bets, db)

    # Only if there are new bets, insert them into the database and send the messages to the Telegram channel
    if new_bets:
        logging.info("New bets found")

        # Insert the new bets into the database
        db.insert_data(new_bets)
        logging.info(f"{len(new_bets)} New bets inserted into the database")

        # Format the bets into messages
        messages = format_messages(bets, BASE_MESSAGE, TIME_ZONE)
        logging.info(
            f"Formatted about {len(messages)} messages to be sent to the Telegram channel"
        )

        # Send the messages to the Telegram channel
        for message in messages:
            send_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message)
            time.sleep(3)

        logging.info(f"Sent all messages to Telegram channel")
    else:
        logging.warning(
            "Duplicate records retrieved from the database...skipping the process"
        )
else:
    logging.warning("No bets retrieved from the API...skipping the process")
