import logging
import datetime
import selector
import json
import update as updater

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
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
from add_stripe_details import create_customer


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

    options = [
        [
            InlineKeyboardButton(
                f"Subscribe to {product['name'].title()}",
                callback_data=product["stripe_product_id"],
            )
        ]
        for product in products
    ]

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
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    user_full_name = query.from_user.full_name
    stripe_product_id = query.data

    selected_product = selector.get_products(stripe_product_id=stripe_product_id)[0]
    product_id = selected_product["id"]
    customers = selector.get_customers(telegram_user_id=user_id)
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

            # If the subscription has not expired, do not create a new subscription
            if expiry_date <= datetime.datetime.now(datetime.UTC):

                await query.answer()
                await query.edit_message_text(
                    text="You already have an active subscription for this product..."
                )
                return

    else:
        customer = {
            "name": user_full_name,
            "telegram_user_id": user_id,
            "telegram_chat_id": chat_id,
            "telegram_temp_payment_message_id": message_id,
            "stripe_customer_id": None,
        }

        selector.create_customers(customer)

        create_customer(customer_info=customer)

    # Update the temporary payment message ID for the customer
    updater.update_temp_payment_message_id(
        telegram_user_id=user_id, temp_payment_message_id=message_id
    )

    # Load the payment link for the product
    base_url = selector.get_base_url()

    await query.delete_message()

    await query.message.reply_text(
        text="Please proceed with the payment by clicking the button below.",
        reply_markup=ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton(
                        text="Pay now",
                        web_app=WebAppInfo(
                            f"{base_url}/payment_link"
                        ),  # TODO: Might pass the product_id here
                    )
                ],
            ]
        ),
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


async def payment_successful(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = json.loads(update.effective_message.web_app_data.data)
    print(data)

    # TODO: Form the personalized links for the user to join the groups
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Received WebApp data: {data}",
        reply_markup=ReplyKeyboardRemove(),
    )


if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    start_handler = CommandHandler("start", start)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)

    # simple start function
    application.add_handler(start_handler)

    # Payment without shipping handler for a specific item
    application.add_handler(
        CallbackQueryHandler(handle_subscription, pattern=r"^prod_.*$")
    )

    # Payment successful handler
    application.add_handler(
        MessageHandler(filters.StatusUpdate.WEB_APP_DATA, payment_successful)
    )

    # unknown command handler
    application.add_handler(unknown_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)
