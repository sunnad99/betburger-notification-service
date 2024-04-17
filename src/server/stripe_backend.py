import sys
import json
import stripe
import datetime
import uuid
import uvicorn
import logging
import pandas as pd
from telegram import Bot
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from .. import database
from ..credentials import (
    NGROK_AUTH_TOKEN,
    STRIPE_AUTH_TOKEN,
    STRIPE_PUBLISHABLE_TOKEN,
    TELEGRAM_AUTH_TOKEN,
    STATIC_DIR,
)
from ..config import (
    ALREADY_ACTIVE_SUBSCRIPTION,
    GOODS_DELIVERY_MESSAGE,
    PAYMENT_CANCELLATION_MESSAGE_TEXT,
)

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


stripe.api_key = STRIPE_AUTH_TOKEN


# Initialize the FastAPI app for a simple web server
templates = Jinja2Templates(directory=STATIC_DIR)
app = FastAPI()


@app.get("/stripe_config")
def secret():
    return JSONResponse({"publishable_key": STRIPE_PUBLISHABLE_TOKEN})


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


@app.get("/payment_link", response_class=HTMLResponse)
def payment_link(
    request: Request, price_id: str, temp_message_id: str, customer_id: str = None
):

    # Construct the data to be passed to the template
    data = {"price_id": price_id, "temp_message_id": temp_message_id}
    if customer_id:
        data["customer_id"] = customer_id

    return templates.TemplateResponse(request=request, name="stripe.html", context=data)


@app.get("/create_checkout_session")
async def create_checkout_session(
    price_id: str,
    web_app_query_id: str,
    temp_message_id: str,
    telegram_user_id: str,
    customer_id: str = None,
):

    telegram_bot = Bot(TELEGRAM_AUTH_TOKEN)

    # Remove the temp message and tell the user that they already have an active subscription
    if customer_id:
        existing_customer = database.selector.get_customers(
            stripe_customer_id=customer_id
        )[0]
        existing_price = database.selector.get_prices(stripe_price_id=price_id)[0]
        subscriptions = database.selector.get_subscriptions(
            customer_id=existing_customer["id"], product_id=existing_price["product_id"]
        )

        if subscriptions:

            await telegram_bot.delete_message(
                chat_id=telegram_user_id, message_id=temp_message_id
            )

            await telegram_bot.answer_web_app_query(
                web_app_query_id,
                {
                    "message_text": ALREADY_ACTIVE_SUBSCRIPTION,
                    "type": "article",
                    "title": "Subscription Already Active",
                    "id": str(uuid.uuid4()),
                },
            )
            return JSONResponse({"error": "Subscription already active..."})

    base_url = database.selector.get_base_url()

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
        "cancel_url": f"{base_url}/cancel_payment?web_app_query_id={web_app_query_id}&session_id={{CHECKOUT_SESSION_ID}}",
    }

    if customer_id:
        session_object["customer"] = customer_id

    try:

        checkout_session = stripe.checkout.Session.create(**session_object)

        return JSONResponse({"session_id": checkout_session.id})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=403)


@app.get("/successful_payment", response_class=HTMLResponse)
async def successful_payment(
    request: Request,
    web_app_query_id: str,
    temp_message_id: str,
    telegram_user_id: str,
    session_id: str,
):
    telegram_bot = Bot(TELEGRAM_AUTH_TOKEN)

    session = stripe.checkout.Session.retrieve(session_id)
    subscription = stripe.Subscription.retrieve(session.get("subscription"))

    customer_id = session.get("customer")
    customer = stripe.Customer.retrieve(customer_id)

    # Need to get the plan from the subscription
    plan = subscription.get("plan")
    if not plan:
        plan = subscription.get("items").data[0].price

    stripe_price_id = plan.get("id")
    selected_price = database.selector.get_prices(stripe_price_id=stripe_price_id)[0]
    selected_product = database.selector.get_products(
        product_id=selected_price.get("product_id")
    )[0]
    groups = database.selector.get_groups(product_id=selected_product.get("id"))

    # Only create a customer if they don't exist in the database
    customers = database.selector.get_customers(stripe_customer_id=customer_id)
    if not customers:
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
        database.selector.create_customers(db_customer)

    # Creating a subscription in the database
    selected_customer = database.selector.get_customers(
        telegram_user_id=telegram_user_id
    )[0]
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

    database.selector.create_subscriptions(
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

    message_to_send = GOODS_DELIVERY_MESSAGE.format(
        links=", \n".join(links),
    )

    # Call the telegram API to send the message to the user
    result = {
        "message_text": message_to_send,
        "type": "article",
        "title": "Successful Payment for Subscribtion",
        "id": str(uuid.uuid4()),
    }

    await telegram_bot.answer_web_app_query(web_app_query_id, result)

    return templates.TemplateResponse(request=request, name="success.html")


@app.get("/cancel_payment", response_class=HTMLResponse)
async def cancel_payment(request: Request, session_id: str, web_app_query_id: str):

    telegram_bot = Bot(TELEGRAM_AUTH_TOKEN)
    stripe.checkout.Session.expire(session_id)

    result = {
        "message_text": PAYMENT_CANCELLATION_MESSAGE_TEXT,
        "type": "article",
        "title": "Payment Cancelled",
        "id": str(uuid.uuid4()),
    }

    await telegram_bot.answer_web_app_query(web_app_query_id, result)

    return templates.TemplateResponse(request=request, name="cancel.html")


if __name__ == "__main__":

    if NGROK_AUTH_TOKEN:
        # pyngrok should only ever be installed or initialized in a dev environment when this flag is set
        from pyngrok import conf, ngrok

        # Get the dev server port (defaults to 8000 for Uvicorn, can be overridden with `--port`
        # when starting the server
        port = (
            sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else "8000"
        )

        # Open a ngrok tunnel to the dev server
        pyngrok_config = conf.PyngrokConfig(region="eu")
        ngrok_tunnel = ngrok.connect(
            port,
            pyngrok_config=pyngrok_config,
            request_header={"add": ["ngrok-skip-browser-warning: true"]},
        )
        public_url = ngrok_tunnel.public_url
        logger.info(f'ngrok tunnel "{public_url}" -> "http://127.0.0.1:{port}"')

        # Update any base URLs or webhooks to use the public ngrok URL
        database.updater.update_ngrok_url(public_url)

    uvicorn.run(app)
