import pytz
import logging
import numpy as np

# Initialize the logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

URL_MAPPING = {19: "https://www.unibet.com/betting/sports/event/{bookmaker_event_link}"}

MIN_ODDS_FACTOR = 0.9
FREQUENCY_SECONDS = 100

# NOTE: The 2nd number in the range is exclusive
# i.e. its not included so e.g. range(1, 5) = [1, 2, 3, 4]
BET_TYPES_TO_FILTER_OUT = {
    "offsides": list(range(223, 229)) + list(range(271, 287)),
}

TIME_ZONE = pytz.timezone("Europe/Stockholm")

PYTHON_TO_SQLITE_DTYPE_MAPPING = {
    np.dtype("int64"): "INTEGER",
    np.dtype("float64"): "REAL",
    np.dtype("object"): "TEXT",
    np.dtype("bool"): "INTEGER",
    np.dtype("datetime64[ns]"): "TEXT",
}

SPORT_EMOJI_MAPPING = {
    "5": "🤾",
    "7": "⚽",
    "8": "🎾",
}

BASE_MESSAGE = """
Nytt Spel!

{sport_emoji} {event_name}
🎲 Bets
{bets}


{league_name}
🔐 Lägsta spelbara odds {min_odds}
🕰️  {match_time}
🌐 {bet_url}
"""

####################### BOT MESSAGES TO USER #######################

BOT_START_MESSAGE = "I'm a bot, please talk to me!"

ALREADY_ACTIVE_SUBSCRIPTION = (
    "You already have an active subscription for this product..."
)

NO_PRODUCTS_AVAILABLE = "No products available at the moment."

PAY_NOW_MESSAGE_TEXT = """Please proceed with the payment by clicking the button below.
{product_description} at a price of {price} {currency} per {interval}.
"""

PAY_NOW_BUTTON_TEXT = "Pay now {price} {currency}"

NO_ACTIVE_SUBSCRIPTIONS_MESSAGE_TEXT = "You don't have any active subscriptions."

## Subscription cancellation messages
SELECT_SUBSCRIPTION_TO_CANCEL_MESSAGE_TEXT = (
    "Please select the subscription you want to cancel."
)

CANCEL_CONFIRMATION_MESSAGE_TEXT = (
    "Are you sure you want to cancel your {product_name} subscription?"
)

PROCEED_WITH_SUBSCRIPTION_CANCELLATION_MESSAGE_TEXT = "Yes"

STOP_SUBSCRIPTION_CANCELLATION_MESSAGE_TEXT = "No"

SUCCESSFUL_SUBSCRIPTION_CANCELLATION_MESSAGE_TEXT = (
    "Your {product_name} subscription has been cancelled."
)

DENIED_SUBSCRIPTION_CANCELLATION_MESSAGE_TEXT = (
    "Your {product_name} subscription has not been cancelled."
)

GOODS_DELIVERY_MESSAGE = """
    Your subscription has been activated.
    The following are the invite links that the admin will have to approve of:

    {links}

    The links will expire after an hour and are only 1 time use.
"""
PAYMENT_CANCELLATION_MESSAGE_TEXT = "The payment was cancelled by the user..."
