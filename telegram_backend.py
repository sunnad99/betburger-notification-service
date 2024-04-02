import logging
import datetime
import selector
import deleter
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

from credentials import TELEGRAM_TOKEN, PAYMENT_PROVIDER_TOKEN

stripe.api_key = PAYMENT_PROVIDER_TOKEN

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
            text="You don't have any active subscriptions.",
        )
        return

    customer = customers[0]
    subscriptions = selector.get_subscriptions(customer_id=customer["id"])
    if not subscriptions:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You don't have any active subscriptions.",
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
        text="Please select the subscription you want to cancel.",
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

    # Confirm the subscription cancellation
    await query.answer()
    await query.edit_message_text(
        text=f"Are you sure you want to cancel your {existing_product['name'].title()} subscription?",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Yes",
                        callback_data=f"confirm_{stripe_subscription_id}",
                    ),
                    InlineKeyboardButton(
                        text="No",
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

    # Let the user know that the subscription has been cancelled
    await query.answer()
    await query.edit_message_text(
        text=f"Your {existing_product['name'].title()} subscription has been cancelled."
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

    # Cancel the subscription cancellation
    await query.answer()
    await query.edit_message_text(
        text=f"Your {existing_product['name'].title()} subscription has not been cancelled."
    )


if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

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
