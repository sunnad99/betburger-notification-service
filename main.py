import time
import logging
import schedule

from database import Database
from config import BASE_MESSAGE, TIME_ZONE, FREQUENCY_MINUTES
from utils import (
    process_bets,
    format_messages,
    load_duplicate_records,
    send_message,
)
import asyncio


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


def main():

    # Connect to the database
    with Database() as db:

        # Obtain the bets from BetBurger
        bets = process_bets(BET_BURGER_TOKEN, BET_BURGER_FILTER_ID)

        # Check if there are any bets retrieved from the API
        if not bets.empty:
            print(list(bets.id))
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

                logging.info(f"Sent {len(messages)} messages to Telegram channel")
            else:
                logging.warning(
                    "Duplicate records retrieved from the database...skipping the process"
                )
        else:
            logging.warning("No bets retrieved from the API...skipping the process")


if __name__ == "__main__":

    # Schedule the task to run every FREQUENCY_MINUTES
    schedule.every(FREQUENCY_MINUTES).minutes.do(main)

    # Run the scheduler in the background
    while True:
        schedule.run_pending()
        time.sleep(1)  # Sleep for 1 second to avoid high CPU usage
