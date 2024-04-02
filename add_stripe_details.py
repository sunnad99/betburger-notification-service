import stripe
import selector
from credentials import STRIPE_AUTH_TOKEN


def create_product(
    name,
    description,
    currency,
    interval,
    interval_count,
    unit_amount,
    unit_label,
    telegram_details=None,
):
    """
    Create a new product in Stripe and store the product information in the database

    Args:
        name: str - Name of the product
        description: str - Description of the product
        currency: str - Currency of the product
        interval: str - Interval for the product
        interval_count: int - Interval count for the product
        unit_amount: int - Unit amount for the product
        unit_label: str - Unit label for the product
        telegram_details: dict - Dictionary containing Telegram group details (group_name and group_id)

    Returns:
        None
    """

    stripe.api_key = STRIPE_AUTH_TOKEN

    product_data = stripe.Product.create(
        name=name,
        description=description,
        default_price_data={
            "currency": currency,
            "recurring": {
                "interval": interval,
                "interval_count": interval_count,
            },
            "unit_amount": unit_amount,
        },
        shippable=False,
        unit_label=unit_label,
    )

    stripe_price_id = product_data["default_price"]
    stripe_product_id = product_data["id"]

    # Store the product information in the database
    product = [
        {
            "name": name,
            "stripe_product_id": stripe_product_id,
            "quantity": 1,
        }
    ]
    selector.create_products(product)
    new_product = selector.get_products(stripe_product_id=stripe_product_id)[0]

    # Store the price information in the database
    price = [
        {
            "stripe_price_id": stripe_price_id,
            "price": unit_amount / 100,
            "currency": currency,
            "product_id": new_product["id"],
        }
    ]
    selector.create_prices(price)

    if telegram_details:

        group = [
            {
                "name": telegram_details["group_name"],
                "telegram_group_id": telegram_details["group_id"],
                "product_id": new_product["id"],
            }
        ]
        selector.create_groups(group)
