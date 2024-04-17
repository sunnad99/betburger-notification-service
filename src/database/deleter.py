import os
import sqlite3
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_NAME = os.path.join(os.path.dirname(__file__), "payments.db")


def delete_subscription(stripe_subscription_id: str):
    """
    Delete a subscription from the database

    Args:
        stripe_subscription_id: str - Stripe subscription ID

    Returns:
        None
    """

    query = f"""
    DELETE FROM subscriptions
    WHERE stripe_subscription_id = '{stripe_subscription_id}'
    """

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()

    except (Exception, sqlite3.DatabaseError) as error:
        logger.error(f"[-] {error}")
        return False
    finally:
        cursor.close()
        conn.close()
