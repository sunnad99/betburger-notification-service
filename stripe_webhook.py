import json
import stripe
import selector
import update
import pandas as pd

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from credentials import PAYMENT_PROVIDER_TOKEN

stripe.api_key = PAYMENT_PROVIDER_TOKEN


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
