import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    filters,
)

from credentials import TELEGRAM_TOKEN, PAYMENT_PROVIDER_TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # TODO: The callback_data for each of the buttons needs to be meaningful for the
    keyboard = [
        [
            InlineKeyboardButton("Subscribe to Unibet", callback_data="unibet"),
        ],
        [
            InlineKeyboardButton("Subscribe to Bet365", callback_data="bet365"),
        ],
    ]

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, please talk to me!",  # TODO: This text needs to be replaced with the actual text for the betting bot
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Selected option: {query.data}")


async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    msg = (
        "Use /shipping to get an invoice for shipping-payment, or /noshipping for an "
        "invoice without shipping."
    )

    await update.message.reply_text(msg)


async def start_without_shipping_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Sends an invoice without shipping-payment."""
    chat_id = update.message.chat_id
    title = "Payment Example"
    description = "Payment Example using python-telegram-bot"
    # select a payload just for you to recognize its the donation from your bot
    payload = "Custom-Payload"
    # In order to get a provider_token see https://core.telegram.org/bots/payments#getting-a-token
    currency = "USD"
    # price in dollars
    price = 1
    # price * 100 so as to include 2 decimal points
    prices = [LabeledPrice("Test", price * 100)]

    # optionally pass need_name=True, need_phone_number=True,
    # need_email=True, need_shipping_address=True, is_flexible=True
    await context.bot.send_invoice(
        chat_id, title, description, payload, PAYMENT_PROVIDER_TOKEN, currency, prices
    )


# after (optional) shipping, it's the pre-checkout
async def precheckout_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Answers the PreQecheckoutQuery"""
    query = update.pre_checkout_query
    # check the payload, is this from your bot?
    if query.invoice_payload != "Custom-Payload":
        # answer False pre_checkout_query
        await query.answer(ok=False, error_message="Something went wrong...")
    else:
        await query.answer(ok=True)


# finally, after contacting the payment provider...
async def successful_payment_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Confirms the successful payment."""
    # do something after successfully receiving payment?

    # TODO: Before sending a message, store the user_id and the payment_id in a database

    await update.message.reply_text(
        "Thank you for your payment!"
    )  # TODO: Send a message that provides the personalized link to the correct betting group


if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # start_handler = CommandHandler("start", start)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    no_shipping_handler = CommandHandler("noshipping", start_without_shipping_callback)
    precheckout_query_handler = PreCheckoutQueryHandler(precheckout_callback)
    succesful_payment_handler = MessageHandler(
        filters.SUCCESSFUL_PAYMENT, successful_payment_callback
    )
    # application.add_handler(start_handler)

    application.add_handler(CallbackQueryHandler(button))

    # simple start function
    application.add_handler(CommandHandler("start", start_callback))

    # Payment without shipping handler
    application.add_handler(no_shipping_handler)

    # Pre-checkout handler to final check
    application.add_handler(precheckout_query_handler)

    # Success! Notify your user!
    application.add_handler(succesful_payment_handler)

    # unknown command handler
    application.add_handler(unknown_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)
