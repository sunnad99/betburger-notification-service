import sqlite3
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_NAME = "payments.db"


def create_customers(customers: list[dict]) -> None:
    """
    Create new customers using an array of dictionaries

    Args:
        customers: list[dict] - List of dictionaries containing customer data

    Returns:
        None
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO customers (
                name,
                telegram_user_id,
                telegram_chat_id,
                telegram_temp_payment_message_id,
                stripe_customer_id
            )
            VALUES (
                :name,
                :telegram_user_id,
                :telegram_chat_id,
                :telegram_temp_payment_message_id,
                :stripe_customer_id
            )
            """,
            customers,
        )
        conn.commit()

    except (Exception, sqlite3.DatabaseError) as error:
        logger.error(f"[-] {error}")
        return False
    finally:
        cursor.close()
        conn.close()


def create_products(products: list[dict]) -> None:
    """
    Create new products using an array of dictionaries

    Args:
        products: list[dict] - List of dictionaries containing product data

    Returns:
        None
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO products (
                name,
                stripe_product_id,
                quantity,
                payment_link
            )
            VALUES (
                :name,
                :stripe_product_id,
                :quantity,
                :payment_link
            )
            """,
            products,
        )
        conn.commit()

    except (Exception, sqlite3.DatabaseError) as error:
        logger.error(f"[-] {error}")
        return False
    finally:
        cursor.close()
        conn.close()


def create_prices(prices: list[dict]) -> None:
    """
    Create new prices using an array of dictionaries

    Args:
        prices: list[dict] - List of dictionaries containing price data

    Returns:
        None
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO prices (
                stripe_price_id,
                product_id,
                unit_amount,
                currency
            )
            VALUES (
                :stripe_price_id,
                :product_id,
                :unit_amount,
                :currency
            )
            """,
            prices,
        )
        conn.commit()

    except (Exception, sqlite3.DatabaseError) as error:
        logger.error(f"[-] {error}")
        return False
    finally:
        cursor.close()
        conn.close()


def create_subscriptions(subscriptions: list[dict]) -> None:
    """
    Create new subscriptions using an array of dictionaries

    Args:
        subscriptions: list[dict] - List of dictionaries containing subscription data

    Returns:
        None
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO subscriptions (
                customer_id,
                product_id,
                price_id,
                stripe_subscription_id,
                subscription_first_date,
                subscription_start_date,
                subscription_expiry_date
            )
            VALUES (
                :customer_id,
                :product_id,
                :price_id,
                :stripe_subscription_id,
                :subscription_first_date,
                :subscription_start_date,
                :subscription_expiry_date
            )
            """,
            subscriptions,
        )
        conn.commit()

    except (Exception, sqlite3.DatabaseError) as error:
        logger.error(f"[-] {error}")
        return False
    finally:
        cursor.close()
        conn.close()


def get_customers(
    telegram_user_id: str = None, stripe_customer_id: str = None
) -> list[dict] | bool:
    """
    Get customers from the database

    Args:
        telegram_user_id: str (Optional) - Telegram user ID
        stripe_customer_id: str (Optional) - Stripe customer ID

    Returns:
        list[dict] | bool - List of dictionaries containing customer data or False if an error occurs
    """

    query = """--sql
    SELECT * FROM customers
    """

    # If user_id is provided, get the customer with that user_id
    if telegram_user_id:
        query += f" WHERE telegram_user_id = '{telegram_user_id}' "
    elif stripe_customer_id:
        query += f" WHERE stripe_customer_id = '{stripe_customer_id}' "

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(query)
        column_names = [column[0] for column in cursor.description]
        fetched_data = [dict(zip(column_names, row)) for row in cursor.fetchall()]

        return fetched_data
    except (Exception, sqlite3.DatabaseError) as error:
        logger.error(f"[-] {error}")
        return False


def get_products(
    product_id: str = None, stripe_product_id: str = None
) -> list[dict] | bool:
    """
    Get products from the database

    Args:
        product_id: str (Optional) - Product ID
        stripe_product_id: str (Optional) - Stripe product ID

    Returns:
        list[dict] | bool - List of dictionaries containing product data or False if an error occurs
    """

    query = """--sql
    SELECT * FROM products
    """

    # If product_id is provided, get the product with that product_id
    if product_id:
        query += f" WHERE id = {product_id}"
    elif stripe_product_id:
        query += f" WHERE stripe_product_id = '{stripe_product_id}'"

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(query)
        return [
            dict(zip([column[0] for column in cursor.description], row))
            for row in cursor.fetchall()
        ]
    except (Exception, sqlite3.DatabaseError) as error:
        logger.error(f"[-] {error}")
        return False
    finally:
        cursor.close()
        conn.close()


def get_prices(
    product_id: str = None, stripe_price_id: str = None
) -> list[dict] | bool:
    """
    Get prices from the database

    Args:
        product_id: str (Optional) - Product ID
        stripe_price_id: str (Optional) - Stripe price ID

    Returns:
        list[dict] | bool - List of dictionaries containing price data or False if an error occurs
    """

    query = """--sql
    SELECT * FROM prices
    """

    # If product_id is provided, get the price with that product_id
    if product_id:
        query += f" WHERE product_id = {product_id}"
    elif stripe_price_id:
        query += f" WHERE stripe_price_id = '{stripe_price_id}'"

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(query)
        return [
            dict(zip([column[0] for column in cursor.description], row))
            for row in cursor.fetchall()
        ]
    except (Exception, sqlite3.DatabaseError) as error:
        logger.error(f"[-] {error}")
        return False
    finally:
        cursor.close()
        conn.close()


def get_subscriptions(
    customer_id: int = None, product_id: int = None
) -> list[dict] | bool:
    """
    Get subscriptions from the database

    Args:
        customer_id: int - Customer ID
        product_id: int - Product ID

    Returns:
        list[dict] | bool - List of dictionaries containing subscription data or False if an error occurs
    """

    query = """--sql
    SELECT * FROM subscriptions
    """

    # If user_id is provided, get the subscription with that customer_id
    if customer_id:
        query += f" WHERE customer_id = {customer_id}"

        # If product_id is provided, get the subscription with that product_id
        if product_id:
            query += f" AND product_id = {product_id}"

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(query)
        return [
            dict(zip([column[0] for column in cursor.description], row))
            for row in cursor.fetchall()
        ]
    except (Exception, sqlite3.DatabaseError) as error:
        logger.error(f"[-] {error}")
        return False
    finally:
        cursor.close()
        conn.close()
