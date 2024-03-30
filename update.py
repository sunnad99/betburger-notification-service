import sqlite3
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_NAME = "payments.db"


def update_temp_payment_message_id(
    telegram_user_id: str, temp_payment_message_id: str
) -> None:
    """
    Update the temporary payment message ID for a customer

    Args:
        telegram_user_id: str - Telegram user ID
        temp_payment_message_id: str - Temporary payment message ID

    Returns:
        None
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE customers
            SET telegram_temp_payment_message_id = :temp_payment_message_id
            WHERE telegram_user_id = :telegram_user_id
            """,
            {
                "telegram_user_id": telegram_user_id,
                "temp_payment_message_id": temp_payment_message_id,
            },
        )
        conn.commit()

    except (Exception, sqlite3.DatabaseError) as error:
        logger.error(f"[-] {error}")
        return False
    finally:
        cursor.close()
        conn.close()
