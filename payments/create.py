import sqlite3
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


DB_NAME = "payments.db"


def create_table_customers() -> None:
    table_name = "customers"
    f"""Create table {table_name} in database bets"""

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            f"""--sql
            CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            telegram_user_id TEXT,
            telegram_chat_id TEXT,
            telegram_temp_payment_message_id TEXT,
            stripe_customer_id TEXT
            );
            """
        )
        conn.commit()
        logger.info(f"[+] Table {table_name} created successfully")

    except (Exception, sqlite3.DatabaseError) as error:
        logger.error(f"[-] {error}")


def create_table_products() -> None:
    table_name = "products"
    f"""Create table {table_name} in database bets"""

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            f"""--sql
            CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            stripe_product_id TEXT,
            quantity INTEGER
            );
            """
        )
        conn.commit()
        logger.info(f"[+] Table {table_name} created successfully")

    except (Exception, sqlite3.DatabaseError) as error:
        logger.error(f"[-] {error}")


def create_table_groups() -> None:
    table_name = "groups"
    f"""Create table {table_name} in database bets"""

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            f"""--sql
            CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            telegram_group_id TEXT,
            product_id REFERENCES products(id) ON UPDATE CASCADE ON DELETE CASCADE
            );
            """
        )
        conn.commit()
        logger.info(f"[+] Table {table_name} created successfully")

    except (Exception, sqlite3.DatabaseError) as error:
        logger.error(f"[-] {error}")


def create_table_price() -> None:
    table_name = "price"
    f"""Create table {table_name} in database bets"""

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            f"""--sql
            CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            stripe_price_id TEXT,
            price REAL,
            currency TEXT,
            product_id REFERENCES products(id) ON UPDATE CASCADE ON DELETE CASCADE
            );
            """
        )
        conn.commit()
        logger.info(f"[+] Table {table_name} created successfully")

    except (Exception, sqlite3.DatabaseError) as error:
        logger.error(f"[-] {error}")


def create_table_subscriptions() -> None:
    table_name = "subscriptions"
    f"""Create table {table_name} in database bets"""

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            f"""--sql
            CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscription_first_date TEXT,
            subscription_start_date TEXT,
            subscription_expiry_date TEXT,
            stripe_subscription_id TEXT,
            customer_id REFERENCES customers(id) ON UPDATE CASCADE ON DELETE CASCADE,
            product_id REFERENCES products(id) ON UPDATE CASCADE ON DELETE CASCADE,
            price_id REFERENCES price(id) ON UPDATE CASCADE ON DELETE CASCADE
            );
            """
        )
        conn.commit()
        logger.info(f"[+] Table {table_name} created successfully")

    except (Exception, sqlite3.DatabaseError) as error:
        logger.error(f"[-] {error}")


if __name__ == "__main__":
    create_table_customers()

    create_table_products()

    create_table_groups()

    create_table_price()

    create_table_subscriptions()
