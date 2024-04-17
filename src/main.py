import time
import logging
import schedule

from database import Database
from config import BASE_MESSAGE, SPORT_EMOJI_MAPPING, TIME_ZONE, FREQUENCY_SECONDS
from utils import (
    process_bets_with_retry,
    format_messages,
    load_duplicate_records,
    insert_new_bets,
    send_message,
)


from credentials import (
    BET_BURGER_TOKEN,
    BET_BURGER_FILTER_ID,
    TELEGRAM_AUTH_TOKEN,
    TELEGRAM_CHAT_MAPPING,
)


def main():

    # Connect to the database
    with Database() as db:

        bets = process_bets_with_retry(BET_BURGER_TOKEN, BET_BURGER_FILTER_ID)

        # Check if there are any bets retrieved from the API
        if not bets.empty:
            print(list(bets.id))
            logging.info(f"{len(bets)} Bets retrieved from the API")

            # Retrieve duplicate records, if they exist, from the database
            new_bets_df = load_duplicate_records(bets, db)

            # Only if there are new bets, insert them into the database and send the messages to the Telegram channel
            if not new_bets_df.empty:
                # Define the mapping between pandas dtypes and SQLite3 dtypes

                logging.info("New bets found")
                new_bets = new_bets_df.to_dict("records")

                # Insert the new bets into the database
                insert_new_bets(db, new_bets_df, new_bets)
                logging.info(f"{len(new_bets)} New bets inserted into the database")

                for sport_id, sport_bets_df in new_bets_df.groupby("sport_id"):

                    sport_id_str = str(sport_id)
                    sport_emoji = SPORT_EMOJI_MAPPING.get(sport_id_str, "")
                    chat_id = TELEGRAM_CHAT_MAPPING.get(sport_id_str)

                    # If the chat_id is not found, don't send the bet
                    if not chat_id:
                        continue

                    # Format the bets into messages
                    messages = format_messages(
                        sport_bets_df, BASE_MESSAGE, TIME_ZONE, sport_emoji
                    )
                    logging.info(
                        f"Formatted about {len(messages)} messages for sport id {sport_id}"
                    )

                    # Send the messages to the Telegram channel
                    for message in messages:

                        send_message(TELEGRAM_AUTH_TOKEN, chat_id, message)
                        time.sleep(3)

                    logging.info(
                        f"Sent {len(messages)} messages to the Telegram channel with id {chat_id}"
                    )
            else:
                logging.warning(
                    "Duplicate records retrieved from the database...skipping the process"
                )
        else:
            logging.warning("No bets retrieved from the API...skipping the process")


if __name__ == "__main__":
    main()
    # # Schedule the task to run every FREQUENCY_MINUTES
    # schedule.every(FREQUENCY_SECONDS).seconds.do(main)

    # # Run the scheduler in the background
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)  # Sleep for 1 second to avoid high CPU usage
