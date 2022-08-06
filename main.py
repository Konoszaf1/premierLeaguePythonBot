""" Python program that compares given predicted premier league tables and compares them to the real table.

Gets live premier league table from skysports website, creates a list of players, calculates the scores based on
team positional differences between the actual table and player tables. Saves player scores and relays them through the
Telegram API.

@authors flamprakis, Konoszaf1
"""

import logging
import telegram
from telegram import ext

import json_readers
import telegram_messaging

BOT_TOKEN = json_readers.get_key("BOT_TOKEN")


def handle_message(update: telegram.Update, context: ext.CallbackContext):
    """Redirects received message with passed arguments to telegram_messaging to handle it according to text."""
    telegram_messaging.handle_received_message(update, context)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    # Setup and run bot
    updater = ext.Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    echo_handler = ext.MessageHandler(ext.Filters.text & (~ext.Filters.command), handle_message)
    dispatcher.add_handler(echo_handler)
    logging.info("Listening...")
    updater.start_polling()
