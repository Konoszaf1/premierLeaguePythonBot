""" File consists of helper functions that facilitate communication with telegram"""
from typing import List

import fixtures
import requests
import telegram
from telegram import ext
from requests_html import HTMLSession
from datetime import datetime, timedelta

import json_readers
import player



def handle_received_message(update: telegram.Update, context: ext.CallbackContext ) -> None:
    """Handle message and respond according to included text."""
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)
    received_text = update.message.text
    bot = context.bot

    if received_text == "test":
        bot.sendMessage()

    if received_text == 'Give score':
        telegram_bot_send_score(bot, update)

    if "fixtures" in received_text.lower():
        fixture_filter = parse_filter(received_text)
        fixtures_list = fixtures.get_fixtures()
        fixtures.write_fixtures(fixtures_list)
        fixtures_list = select_fixtures(fixtures_list,fixture_filter)
        messages = format_fixtures_message(fixtures_list)
        for message in messages:
            bot.sendMessage(update.effective_chat.id, message)

def parse_filter(message:str) -> datetime:
    if "today" in message or "when" not in message:
        return datetime.today()
    message = message[message.index("when")+5:].strip()
    if "tomorrow" in message:
        return datetime.today() + timedelta(days=1)
    elif "." in message:
        try:
            return datetime.strptime(message, "%d.%m.%Y")
        except ValueError:
            return datetime.today()

def select_fixtures(fixtures_list, filter:datetime) -> List[fixtures.Fixture]:
    def check_same_day(test:fixtures.Fixture):
        if filter.day == test.match_datetime.day \
                and filter.month == test.match_datetime.month \
                and filter.year == test.match_datetime.year:
            return True
        return False
    fixtures_list = [x for x in fixtures_list if check_same_day(x)]
    return fixtures_list


def format_fixtures_message(fixtures_list: List[fixtures.Fixture]):
    return_messages_list = []
    return_message = ""
    for index, fix in enumerate(fixtures_list):
        if index != 0 and index % 4 == 0:
            return_messages_list.append(return_message)
            return_message = ""
        return_message += (str(fix) + "\n\n")
    return return_messages_list


def telegram_bot_send_score(bot: telegram.Bot, update: telegram.Update) -> None:
    """Send score via Telegram API"""
    players = player.create_player_objects(*json_readers.get_player_data_and_player_tables())
    message = "".join([x.generate_telegram_string() for x in players])
    bot_chat_id = update.effective_chat.id
    text = f"Update {datetime.today().strftime('%d.%m.%Y')}\n\n" \
           f"{message}"
    json_readers.update_players_scores(players) if len(players) > 0 else None
    bot.sendMessage(bot_chat_id, text)
