import logging
import datetime
import selector
import pandas as pd

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from credentials import TELEGRAM_TOKEN


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start function for the bot to start the subscription process

    Args:
        update: Update - The update object
        context: ContextTypes.DEFAULT_TYPE - The context object

    Returns:
        None
    """

    products = selector.get_products()

    # If there are no products, tell the user that there are no products available
    if not products:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="No products available at the moment.",
        )
        return

    options = []
    prices = selector.get_prices()
    for product in products:
        price = next(filter(lambda price: product["id"] == price["product_id"], prices))
        button = [
            InlineKeyboardButton(
                f"Subscribe to {product['name'].title()}",
                callback_data=price["stripe_price_id"],
            )
        ]
        options.append(button)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, please talk to me!",  # TODO: This text needs to be replaced with the actual text for the betting bot
        reply_markup=InlineKeyboardMarkup(options),
    )


async def handle_subscription(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle the subscription process for a product

    Args:
        update: Update - The update object
        context: ContextTypes.DEFAULT_TYPE - The context object

    Returns:
        None
    """

    query = update.callback_query
    user_id = query.from_user.id
    stripe_price_id = query.data
    message_id = query.message.message_id

    selected_price = selector.get_prices(stripe_price_id=stripe_price_id)[0]
    selected_product = selector.get_products(product_id=selected_price["product_id"])[0]
    customers = selector.get_customers(telegram_user_id=user_id)

    product_id = selected_product["id"]
    if customers:

        existing_customer = customers[0]
        # Check if the customer has an active subscription
        customer_id = existing_customer["id"]
        subscriptions = selector.get_subscriptions(
            customer_id=customer_id, product_id=product_id
        )
        if subscriptions:
            # Check if the subscription is still active
            existing_subscription = subscriptions[0]
            expiry_date = existing_subscription["subscription_expiry_date"]

            # Don't allow the user to subscribe if they already have an active subscription
            if pd.to_datetime(expiry_date, utc=True) <= datetime.datetime.now(
                datetime.timezone.utc
            ):

                await query.answer()
                await query.edit_message_text(
                    text="You already have an active subscription for this product..."
                )
                return

    # Load the payment link for the backend and create a payment link
    base_url = selector.get_base_url()
    stripe_price_id = selected_price["stripe_price_id"]
    payment_url = f"{base_url}/payment_link?temp_message_id={message_id}&price_id={stripe_price_id}"
    if customers:
        payment_url += f"&customer_id={customers[0].get('stripe_customer_id')}"

    await query.answer()
    await query.edit_message_text(
        text="Please proceed with the payment by clicking the button below.",  # TODO: Move this text to config file
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Pay now",
                        web_app=WebAppInfo(payment_url),
                    )
                ],
            ]
        ),
    )


if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    start_handler = CommandHandler("start", start)

    # simple start function
    application.add_handler(start_handler)

    # Payment without shipping handler for a specific item
    application.add_handler(
        CallbackQueryHandler(handle_subscription, pattern=r"^price_.*$")
    )

    application.run_polling(allowed_updates=Update.ALL_TYPES)
