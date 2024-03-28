import json
import stripe
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

    # Handle the event
    if event.type == "payment_intent.succeeded":
        payment_intent = event.data.object  # contains a stripe.PaymentIntent
        print("PaymentIntent was successful!")
        print(payment_intent)
    elif event.type == "payment_method.attached":
        payment_method = event.data.object  # contains a stripe.PaymentMethod
        print("PaymentMethod was attached to a Customer!")
    # ... handle other event types
    else:
        print("Unhandled event type {}".format(event.type))

    return JSONResponse(content={}, status_code=200)
