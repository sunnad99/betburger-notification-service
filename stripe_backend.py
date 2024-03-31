import os
import sys
import json
import stripe
import uvicorn
import logging
import sqlite3
import selector
import update

import pandas as pd

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from credentials import PAYMENT_PROVIDER_TOKEN

# Set up logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


stripe.api_key = PAYMENT_PROVIDER_TOKEN


# Initialize the FastAPI app for a simple web server
app = FastAPI()


@app.post("/payment_webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    event = None

    try:
        event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        # Invalid payload
        return JSONResponse(status_code=400)

    if event.type == "customer.subscription.created":
        subscription = event.data.object  # contains a stripe.PaymentIntent
        print("PaymentIntent was successful!")
        customer_id = subscription.get("customer")

        print("Customer ID: ", customer_id)

        # If there is no customer_id, then there is no customer
        if not customer_id:
            return JSONResponse(
                content={"message": "No customer recorded"}, status_code=200
            )

        # Need to get the plan from the subscription
        plan = subscription.get("plan")
        if not plan:
            plan = subscription.get("items").data[0].price

        product_id = plan.get("product")
        price_id = plan.get("id")

        customers = selector.get_customers(stripe_customer_id=customer_id)
        products = selector.get_products(stripe_product_id=product_id)
        prices = selector.get_prices(stripe_price_id=price_id)

        customer = customers[0]
        product = products[0]
        price = prices[0]

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
                    "customer_id": customer.get("id"),
                    "product_id": product.get("id"),
                    "price_id": price.get("id"),
                    "stripe_subscription_id": subscription_id,
                    "subscription_first_date": subscription_first_date,
                    "subscription_start_date": subscription_start_date,
                    "subscription_expiry_date": subscription_expiry_date,
                }
            ]
        )

    elif event.type == "payment_intent.succeeded":
        payment_intent = event.data.object

        # Get the customer id from the payment intent
        customer_id = payment_intent.get("customer")

        # If there is no customer_id, then there is no customer
        if not customer_id:
            return JSONResponse(
                content={"message": "No customer recorded"}, status_code=200
            )
        # Get the customer details from the database
        customers = selector.get_customers(stripe_customer_id=customer_id)
        if not customers:
            return JSONResponse(
                content={"message": "No customer found"}, status_code=200
            )

        existing_customer = customers[0]
        # TODO: Remove the message from the telegram to prevent the user from paying again
        temp_payment_message_id = existing_customer.get(
            "telegram_temp_payment_message_id"
        )

        # Update the temp payment message id to be null
        update.update_temp_payment_message_id(
            telegram_user_id=existing_customer.get("telegram_user_id"),
            temp_payment_message_id=None,
        )

        # TODO: Send the message to the user
        # to let them know that the subscription was successful and provide them the links for the groups

    elif event.type == "payment_intent.failed":
        pass

    elif event.type == "payment_method.attached":
        payment_method = event.data.object  # contains a stripe.PaymentMethod
        print("PaymentMethod was attached to a Customer!")
    # ... handle other event types
    else:
        print("Unhandled event type {}".format(event.type))

    return JSONResponse(content={}, status_code=200)


@app.post("/secret")
def secret():
    intent = {}  # ... Create or retrieve the PaymentIntent
    return JSONResponse({"client_secret": intent.client_secret})


@app.get("/payment_link")
def payment_link():
    return HTMLResponse(
        """
        <!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Subscription Payment</title>
    <script src="https://js.stripe.com/v3/"></script>
</head>

<body>
    <h1>Subscription Payment</h1>
    <form id="payment-form">
        <div>
            <label for="card-element">
                Credit or debit card
            </label>
            <div id="card-element">
                <!-- A Stripe Element will be inserted here. -->
            </div>
            <!-- Used to display form errors. -->
            <div id="card-errors" role="alert"></div>
        </div>
        <button id="submit">
            Pay
        </button>
    </form>

    <script>
        // Set your publishable key
        const publishableKey = "pk_test_51OyIs4Dvoc9trV896kbQUbY3f8u8cmHmwI4u5yVvkJjCO1sbt0PujfcBNnvcbPYR0UB4hqlzlwU1BzplpvCEkjwZ00Eg7mNjJ5";
        var stripe = Stripe(publishableKey);
        var elements = stripe.elements();

        // Create an instance of the card Element.
        var card = elements.create('card');

        // Add an instance of the card Element into the `card-element` div.
        card.mount('#card-element');

        // Handle real-time validation errors from the card Element.
        card.addEventListener('change', function (event) {
            var displayError = document.getElementById('card-errors');
            if (event.error) {
                displayError.textContent = event.error.message;
            } else {
                displayError.textContent = '';
            }
        });

        // Handle form submission.
        var form = document.getElementById('payment-form');
        form.addEventListener('submit', function (event) {
            event.preventDefault();
            stripe.createToken(card).then(function (result) {
                if (result.error) {
                    // Inform the user if there was an error.
                    var errorElement = document.getElementById('card-errors');
                    errorElement.textContent = result.error.message;
                } else {
                    // Send the token to your server to charge the user.
                    stripeTokenHandler(result.token);
                }
            });
        });

        // Submit the form with the token ID.
        function stripeTokenHandler(token) {
            // You can send the token to your server to create a subscription
            // Use fetch or another AJAX method to send the token to your server
            console.log(token);
        }
    </script>
</body>

</html>

    """
    )


# Helper function to communicate ngrok URL to telegram bot
def update_ngrok_url(base_url: str) -> None:

    conn = sqlite3.connect("backend.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            id PRIMARY KEY,
            name TEXT,
            value TEXT
            )
        """
    )

    cursor.execute(
        """
        UPDATE settings
        SET value = :ngrok_url
        WHERE name = "base_url"
        """,
        {"ngrok_url": base_url},
    )
    if cursor.rowcount == 0:
        cursor.execute(
            """
            INSERT INTO settings (name, value)
            VALUES ("base_url", :ngrok_url)
            """,
            {"ngrok_url": base_url},
        )
    conn.commit()


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
        update_ngrok_url(public_url)

    uvicorn.run(app)
