import stripe
import selector
from credentials import PAYMENT_PROVIDER_TOKEN


def create_product(
    name, description, currency, interval, interval_count, unit_amount, unit_label
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

    Returns:
        None
    """

    stripe.api_key = PAYMENT_PROVIDER_TOKEN

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

    price_id = product_data["default_price"]

    payment_link = stripe.PaymentLink.create(
        line_items=[{"price": price_id, "quantity": 1}],
    )

    product = [
        {
            "name": name,
            "stripe_product_id": product_data["id"],
            "quantity": 1,
            "payment_link": payment_link["url"],
        }
    ]

    selector.create_products(product)


def create_customer(customer_info):
    """
    Create a new customer in Stripe and store the customer information in the database

    Args:
        customer_info: dict - Dictionary containing customer information

    Returns:
        None
    """

    print(PAYMENT_PROVIDER_TOKEN)
    stripe.api_key = PAYMENT_PROVIDER_TOKEN

    name = customer_info["name"]

    customer = stripe.Customer.create(
        name=name,
    )

    customer_info["stripe_customer_id"] = customer["id"]
    customer = [customer_info]

    selector.create_customers(customer)
