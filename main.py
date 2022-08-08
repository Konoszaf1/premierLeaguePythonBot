""" Python program that compares given predicted premier league tables and compares them to the real table.

Gets live premier league table from skysports.com website, creates a list of players, calculates the scores based on
team positional differences between the actual table and player tables. Saves player scores and relays them through the
Telegram API.

@authors flamprakis, Konoszaf1
"""
import datetime
import logging

import pytz
import telegram
from telegram import ext

import json_readers
import telegram_messaging

BOT_TOKEN = json_readers.get_key("BOT_TOKEN")
GROUP_CHAT_ID = json_readers.get_key("GROUP_CHAT_ID")


def handle_message(update: telegram.Update, context: ext.CallbackContext):
    """Redirects received message with passed arguments to telegram_messaging to handle it according to text."""
    telegram_messaging.handle_received_message(update, context)

def send_score_job(context: telegram.ext.CallbackContext):
    """Job to send the score leaderboards to the group chat every day at 23:00 GMT+2"""
    telegram_messaging.telegram_bot_send_score(context.bot, chat_id=GROUP_CHAT_ID)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    # Setup and run bot
    updater = ext.Updater(token=BOT_TOKEN, use_context=True)
    job_queue: ext.JobQueue = updater.job_queue
    job_minute = job_queue.run_daily(send_score_job,
                                     datetime.time(hour=23, minute=00, tzinfo=pytz.timezone('Europe/Athens')),
                                     days=tuple(range(7)))
    dispatcher = updater.dispatcher
    message_handler = ext.MessageHandler(ext.Filters.text & (~ext.Filters.command), handle_message)
    dispatcher.add_handler(message_handler)
    logging.info("Listening...")
    updater.start_polling()
    updater.idle()
