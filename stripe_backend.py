import os
import sys
import json
import stripe
import requests
import datetime
import uuid
import uvicorn
import logging
import selector
import updater
import pandas as pd

from telegram import Bot
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from credentials import PAYMENT_PROVIDER_TOKEN, TELEGRAM_TOKEN

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


stripe.api_key = PAYMENT_PROVIDER_TOKEN


# Initialize the FastAPI app for a simple web server
templates = Jinja2Templates(directory=os.getenv("STATIC_DIR", "./"))
app = FastAPI()


@app.get("/stripe_config")
def secret():
    return JSONResponse({"publishable_key": os.getenv("STRIPE_PUBLISHABLE_KEY")})


@app.get("/payment_link", response_class=HTMLResponse)
def payment_link(
    request: Request, price_id: str, temp_message_id: str, customer_id: str = None
):

    # Construct the data to be passed to the template
    data = {"price_id": price_id, "temp_message_id": temp_message_id}
    if customer_id:
        data["customer_id"] = customer_id

    return templates.TemplateResponse(request=request, name="stripe.html", context=data)


@app.get("/successful_payment", response_class=HTMLResponse)
async def successful_payment(
    request: Request,
    web_app_query_id: str,
    temp_message_id: str,
    telegram_user_id: str,
    session_id: str,
):
    telegram_bot = Bot(TELEGRAM_TOKEN)

    session = stripe.checkout.Session.retrieve(session_id)
    subscription = stripe.Subscription.retrieve(session.get("subscription"))

    customer_id = session.get("customer")
    customer = stripe.Customer.retrieve(customer_id)

    # Need to get the plan from the subscription
    plan = subscription.get("plan")
    if not plan:
        plan = subscription.get("items").data[0].price

    stripe_price_id = plan.get("id")
    selected_price = selector.get_prices(stripe_price_id=stripe_price_id)[0]
    selected_product = selector.get_products(
        product_id=selected_price.get("product_id")
    )[0]
    groups = selector.get_groups(product_id=selected_product.get("id"))

    # Creating a customer in the database
    db_customer = [
        {
            "name": customer.get("name"),
            "telegram_user_id": telegram_user_id,
            "telegram_chat_id": telegram_user_id,
            "telegram_temp_payment_message_id": None,
            "stripe_customer_id": customer_id,
        }
    ]
    selector.create_customers(db_customer)

    # Creating a subscription in the database

    selected_customer = selector.get_customers(telegram_user_id=telegram_user_id)[0]
    (
        subscription_id,
        subscription_first_date,
        subscription_start_date,
        subscription_expiry_date,
    ) = (
        subscription.get("id"),
        pd.to_datetime(subscription.get("start_date"), unit="s").strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        pd.to_datetime(subscription.get("current_period_start"), unit="s").strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        pd.to_datetime(subscription.get("current_period_end"), unit="s").strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
    )

    selector.create_subscriptions(
        [
            {
                "customer_id": selected_customer.get("id"),
                "product_id": selected_product.get("id"),
                "price_id": selected_price.get("id"),
                "stripe_subscription_id": subscription_id,
                "subscription_first_date": subscription_first_date,
                "subscription_start_date": subscription_start_date,
                "subscription_expiry_date": subscription_expiry_date,
            }
        ]
    )

    # Delete the temporary message that was sent to the user
    await telegram_bot.delete_message(
        chat_id=telegram_user_id, message_id=temp_message_id
    )

    # Craft the message to be sent to the user
    links = []
    for group in groups:

        group_id = group["telegram_group_id"]
        expiry_time = int(
            (
                datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
            ).timestamp()
        )  # TODO: Make this editable in the config.py file
        params = {
            "chat_id": group_id,
            "expire_date": expiry_time,
            "creates_join_request": True,
        }

        try:
            chat_link = await telegram_bot.create_chat_invite_link(**params)
            links.append(chat_link.invite_link)
        except Exception as e:
            logger.error(
                f"Error creating invite link for group {group_id}...the bot must exist in the group: {e}"
            )
            links.append("N/A")

    links_str = ", ".join(links)

    # TODO: Make the following message editable in the config files
    message_to_send = f"""
    The following are the invite links that the admin will have to approve of:

        {links_str}
    """

    # Call the telegram API to send the message to the user
    params = {
        "web_app_query_id": web_app_query_id,
        "result": json.dumps(
            {
                "message_text": message_to_send,
                "type": "article",
                "title": "Successful Payment for Subscribtion",
                "id": str(uuid.uuid4()),
            }
        ),
    }

    response = requests.request(
        "POST",
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerWebAppQuery",
        params=params,
    )

    if response.status_code == 200:
        print("Message sent successfully: ", response.text)
    else:
        print("Error sending message: ", response.text)

    return templates.TemplateResponse(request=request, name="success.html")


@app.get("/create_checkout_session")
def create_checkout_session(
    price_id: str,
    web_app_query_id: str,
    temp_message_id: str,
    telegram_user_id: str,
    customer_id: str = None,
):

    # TODO: Make sure not let the user pay for the same subscription twice

    base_url = selector.get_base_url()

    session_object = {
        "payment_method_types": ["card"],
        "line_items": [
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
        "mode": "subscription",
        "success_url": f"{base_url}/successful_payment?web_app_query_id={web_app_query_id}&temp_message_id={temp_message_id}&telegram_user_id={telegram_user_id}&session_id={{CHECKOUT_SESSION_ID}}",
    }

    if customer_id:
        session_object["customer"] = customer_id

    try:

        checkout_session = stripe.checkout.Session.create(**session_object)

        return JSONResponse({"session_id": checkout_session.id})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=403)


@app.post("/payment_webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    event = None

    try:
        event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        # Invalid payload
        return JSONResponse(status_code=400)

    if event.type == "payment_intent.succeeded":
        payment_intent = event.data.object

        print("PaymentIntent was successful!")

    elif event.type == "payment_intent.failed":
        pass

    elif event.type == "payment_method.attached":
        payment_method = event.data.object  # contains a stripe.PaymentMethod
        print("PaymentMethod was attached to a Customer!")
    # ... handle other event types
    else:
        print("Unhandled event type {}".format(event.type))

    return JSONResponse(content={}, status_code=200)


# Helper function to communicate ngrok URL to telegram bot


if __name__ == "__main__":

    USE_NGROK = os.environ.get("USE_NGROK", "False") == "True"
    NGROK_AUTHTOKEN = os.environ.get("NGROK_AUTHTOKEN")
    if USE_NGROK and NGROK_AUTHTOKEN:
        # pyngrok should only ever be installed or initialized in a dev environment when this flag is set
        from pyngrok import ngrok

        # Get the dev server port (defaults to 8000 for Uvicorn, can be overridden with `--port`
        # when starting the server
        port = (
            sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else "8000"
        )

        # Open a ngrok tunnel to the dev server
        public_url = ngrok.connect(port).public_url
        logger.info(f'ngrok tunnel "{public_url}" -> "http://127.0.0.1:{port}"')

        # Update any base URLs or webhooks to use the public ngrok URL
        updater.update_ngrok_url(public_url)

    uvicorn.run(app)
