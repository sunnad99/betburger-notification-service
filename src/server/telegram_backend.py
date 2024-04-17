import logging
import datetime
from . import selector, deleter
import pandas as pd
import stripe

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
    CallbackQueryHandler,
)

from ..credentials import TELEGRAM_AUTH_TOKEN, STRIPE_AUTH_TOKEN

from ..config import (
    BOT_START_MESSAGE,
    ALREADY_ACTIVE_SUBSCRIPTION,
    CANCEL_CONFIRMATION_MESSAGE_TEXT,
    DENIED_SUBSCRIPTION_CANCELLATION_MESSAGE_TEXT,
    NO_ACTIVE_SUBSCRIPTIONS_MESSAGE_TEXT,
    NO_PRODUCTS_AVAILABLE,
    PAY_NOW_BUTTON_TEXT,
    PAY_NOW_MESSAGE_TEXT,
    PROCEED_WITH_SUBSCRIPTION_CANCELLATION_MESSAGE_TEXT,
    SELECT_SUBSCRIPTION_TO_CANCEL_MESSAGE_TEXT,
    STOP_SUBSCRIPTION_CANCELLATION_MESSAGE_TEXT,
    SUCCESSFUL_SUBSCRIPTION_CANCELLATION_MESSAGE_TEXT,
)

stripe.api_key = STRIPE_AUTH_TOKEN

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
            text=NO_PRODUCTS_AVAILABLE,
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
        text=BOT_START_MESSAGE,
        reply_markup=InlineKeyboardMarkup(options),
    )


async def handle_start_subscription(
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
            if pd.to_datetime(expiry_date, utc=True) >= datetime.datetime.now(
                datetime.timezone.utc
            ):

                await query.answer()
                await query.edit_message_text(text=ALREADY_ACTIVE_SUBSCRIPTION)
                return

    # Load the payment link for the backend and create a payment link
    base_url = selector.get_base_url()
    stripe_price_id = selected_price["stripe_price_id"]
    payment_url = f"{base_url}/payment_link?temp_message_id={message_id}&price_id={stripe_price_id}"
    if customers:
        payment_url += f"&customer_id={customers[0].get('stripe_customer_id')}"

    pay_now_message_text = PAY_NOW_MESSAGE_TEXT.format(
        product_description=selected_product["name"],
        price=round(selected_price["price"]),
        currency=selected_price["currency"].upper(),
        interval="month",
    )

    pay_now_button_text = PAY_NOW_BUTTON_TEXT.format(
        price=round(selected_price["price"]),
        currency=selected_price["currency"].upper(),
    )

    await query.answer()
    await query.edit_message_text(
        text=pay_now_message_text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=pay_now_button_text,
                        web_app=WebAppInfo(payment_url),
                    )
                ],
            ]
        ),
    )


async def cancel_subscription(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Cancel the subscription process for a product

    Args:
        update: Update - The update object
        context: ContextTypes.DEFAULT_TYPE - The context object

    Returns:
        None
    """
    user_id = update.effective_user.id
    customers = selector.get_customers(telegram_user_id=user_id)

    if not customers:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=NO_ACTIVE_SUBSCRIPTIONS_MESSAGE_TEXT,
        )
        return

    customer = customers[0]
    subscriptions = selector.get_subscriptions(customer_id=customer["id"])
    if not subscriptions:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=NO_ACTIVE_SUBSCRIPTIONS_MESSAGE_TEXT,
        )
        return

    options = []
    for subscription in subscriptions:
        product = selector.get_products(product_id=subscription["product_id"])[0]
        button = [
            InlineKeyboardButton(
                f"Cancel {product['name'].title()} subscription",
                callback_data=subscription["stripe_subscription_id"],
            )
        ]
        options.append(button)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=SELECT_SUBSCRIPTION_TO_CANCEL_MESSAGE_TEXT,
        reply_markup=InlineKeyboardMarkup(options),
    )


async def confirm_subscription_cancellation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Confirm the subscription cancellation process for a product

    Args:
        update: Update - The update object
        context: ContextTypes.DEFAULT_TYPE - The context object

    Returns:
        None
    """

    query = update.callback_query
    stripe_subscription_id = query.data

    existing_subscription = selector.get_subscriptions(
        stripe_subscription_id=stripe_subscription_id
    )[0]
    existing_product = selector.get_products(
        product_id=existing_subscription["product_id"]
    )[0]

    cancel_confirmation_message_text = CANCEL_CONFIRMATION_MESSAGE_TEXT.format(
        product_name=existing_product["name"].title()
    )

    # Confirm the subscription cancellation
    await query.answer()
    await query.edit_message_text(
        text=cancel_confirmation_message_text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=PROCEED_WITH_SUBSCRIPTION_CANCELLATION_MESSAGE_TEXT,
                        callback_data=f"confirm_{stripe_subscription_id}",
                    ),
                    InlineKeyboardButton(
                        text=STOP_SUBSCRIPTION_CANCELLATION_MESSAGE_TEXT,
                        callback_data=f"cancel_{stripe_subscription_id}",
                    ),
                ],
            ]
        ),
    )


async def handle_end_subscription(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle the end subscription process for a product

    Args:
        update: Update - The update object
        context: ContextTypes.DEFAULT_TYPE - The context object

    Returns:
        None
    """

    query = update.callback_query
    stripe_subscription_id = query.data.replace("confirm_", "")

    existing_subscription = selector.get_subscriptions(
        stripe_subscription_id=stripe_subscription_id
    )[0]
    existing_product = selector.get_products(
        product_id=existing_subscription["product_id"]
    )[0]

    # Cancel the subscription from stripe and remove it from the database
    stripe.Subscription.delete(stripe_subscription_id)
    deleter.delete_subscription(stripe_subscription_id)

    successful_subscription_cancellation_message_text = (
        SUCCESSFUL_SUBSCRIPTION_CANCELLATION_MESSAGE_TEXT.format(
            product_name=existing_product["name"].title()
        )
    )

    # Let the user know that the subscription has been cancelled
    await query.answer()
    await query.edit_message_text(
        text=successful_subscription_cancellation_message_text
    )


async def cancel_subscription_cancellation(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Cancel the subscription cancellation process for a product

    Args:
        update: Update - The update object
        context: ContextTypes.DEFAULT_TYPE - The context object

    Returns:
        None
    """

    query = update.callback_query
    stripe_subscription_id = query.data.replace("cancel_", "")

    existing_subscription = selector.get_subscriptions(
        stripe_subscription_id=stripe_subscription_id
    )[0]
    existing_product = selector.get_products(
        product_id=existing_subscription["product_id"]
    )[0]

    denied_subscription_cancellation_message_text = (
        DENIED_SUBSCRIPTION_CANCELLATION_MESSAGE_TEXT.format(
            product_name=existing_product["name"].title()
        )
    )

    # Cancel the subscription cancellation
    await query.answer()
    await query.edit_message_text(text=denied_subscription_cancellation_message_text)


if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_AUTH_TOKEN).build()

    start_subscription_handler = CommandHandler("start", start)

    handle_start_subscription_handler = CallbackQueryHandler(
        handle_start_subscription, pattern=r"^price_.*$"
    )

    end_subscription_handler = CommandHandler("endSubscription", cancel_subscription)

    confirm_subscription_cancellation_handler = CallbackQueryHandler(
        confirm_subscription_cancellation, pattern=r"^sub_.*$"
    )

    cancel_subscription_cancellation_handler = CallbackQueryHandler(
        cancel_subscription_cancellation, pattern=r"^cancel_sub_.*$"
    )

    handle_end_subscription_handler = CallbackQueryHandler(
        handle_end_subscription, pattern=r"^confirm_sub_.*$"
    )

    ### Subscription process ###

    # Start subscription process
    application.add_handler(start_subscription_handler)

    # Handling the start subscription process
    application.add_handler(handle_start_subscription_handler)

    ### Subscription cancellation process ###

    # End subscription process
    application.add_handler(end_subscription_handler)

    # Confirming the subscription cancellation
    application.add_handler(confirm_subscription_cancellation_handler)

    # Cancelling the subscription cancellation
    application.add_handler(cancel_subscription_cancellation_handler)

    # Handling the end subscription process
    application.add_handler(handle_end_subscription_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)
