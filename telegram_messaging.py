""" File consists of helper functions that facilitate communication with telegram"""
from typing import List

import fixtures
import requests
import telegram
from telegram import ext, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, Message
from requests_html import HTMLSession
from datetime import datetime, timedelta

import json_readers
import player


def handle_received_message(update: telegram.Update, context: ext.CallbackContext) -> None:
    """Handle message and respond according to included text."""
    # context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text, reply_markup=get_inline_keyboard())
    received_text = update.message.text
    bot = context.bot
    fixtures_list = []
    if received_text.lower() == "start":  # Start Bot Session send menu including "Fixtures" and "Score"
        message_to_be_deleted = update.message.reply_text(text="Starting Bot...", reply_markup=get_inline_keyboard())
        bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
    elif "exit" in received_text.lower():  # Exit Bot Session send menu including "Fixtures" and "Score"
        message_to_be_deleted = update.message.reply_text(text="Starting Bot...",
                                                          reply_markup=telegram.ReplyKeyboardRemove())
        bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        bot.delete_message(chat_id=message_to_be_deleted.chat_id, message_id=message_to_be_deleted.message_id)
    elif received_text == 'Score':  # Send current prediction score as a message
        next_message = telegram_bot_send_score(bot, update)
        bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
    elif "fixtures" in received_text.lower():  # Send Fixtures Menu and allow players to bet by clicking on button
        fixtures_list = fixtures.get_fixtures()
        update.message.reply_text(text=f"Fixtures for {datetime.today().strftime('%d.%m.%Y')}",
                                  reply_markup=generate_fixture_keyboard_markup(fixtures_list, update,
                                                                                date_to_filter=datetime.today()))
        bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        fixtures.write_fixtures(fixtures_list)
    elif received_text.lower() == "tomorrow":
        fixtures_list = fixtures.load_fixtures()
        previous_message = update.message.reply_to_message
        previous_date = datetime.strptime(previous_message.text[previous_message.text.rindex(" "):].strip(), '%d.%m.%Y')
        next_date = previous_date+timedelta(days=1)
        update.message.reply_text(text=f"Fixtures for {next_date.strftime('%d.%m.%Y')}",reply_markup=generate_fixture_keyboard_markup(fixtures_list, update,next_date ))
        bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
    else:
        fixtures_list = fixtures.load_fixtures()
        betted_fixture = None
        previous_date = datetime.today()
        if "for" in received_text:
            previous_message = update.message.reply_to_message
            previous_date = datetime.strptime(previous_message.text[previous_message.text.rindex(" "):].strip(), '%d.%m.%Y')
        if ((received_text in ([x.home_team for x in fixtures_list] + [x.away_team for x in fixtures_list]))
                or ('X' in received_text and received_text[received_text.index('\n') + 1:] in [x.id for x in
                                                                                               fixtures_list])):
            previous_message = update.message.reply_to_message
            previous_date = datetime.strptime(previous_message.text[previous_message.text.rindex(" "):].strip(), '%d.%m.%Y')
            temp_fixtures_list = select_fixtures(fixtures_list, previous_date)
            if 'X' not in received_text:
                betted_fixture = [x for x in temp_fixtures_list if x.home_team == received_text or x.away_team == received_text][0]
                betted_fixture.predictions_dict[json_readers.get_player_name_by_id(update.message.from_user["id"])] = \
                '1' if received_text in [x.home_team for x in temp_fixtures_list] else '2'
            else:
                id = received_text[received_text.index('\n') + 1:]
                betted_fixture = [x for x in temp_fixtures_list if x.id == id][0]
                betted_fixture.predictions_dict[json_readers.get_player_name_by_id(update.message.from_user["id"])] = 'X'
            fixtures_list.remove(betted_fixture)
            fixtures_list.append(betted_fixture)
            fixtures.write_fixtures(fixtures_list)
        update.message.reply_text(text=f"Fixtures for {previous_date.strftime('%d.%m.%Y')}", reply_markup=generate_fixture_keyboard_markup(fixtures_list, update, previous_date))
        bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
def parse_filter(message: str) -> datetime:
    if "today" in message or "when" not in message:
        return datetime.today()
    message = message[message.index("when") + 5:].strip()
    if "tomorrow" in message:
        return datetime.today() + timedelta(days=1)
    elif "." in message:
        try:
            return datetime.strptime(message, "%d.%m.%Y")
        except ValueError:
            return datetime.today()


def select_fixtures(fixtures_list, filter: datetime) -> List[fixtures.Fixture]:
    def check_same_day(test: fixtures.Fixture):
        if filter.day == test.match_datetime.day \
                and filter.month == test.match_datetime.month \
                and filter.year == test.match_datetime.year\
                and filter.hour < test.match_datetime.hour\
                and filter.minute < test.match_datetime.minute:
            return True
        return False

    fixtures_list = [x for x in fixtures_list if check_same_day(x)]
    fixtures_list.sort(key=fixtures.sort_key)
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


def telegram_bot_send_score(bot: telegram.Bot, update: telegram.Update) -> Message:
    """Send score via Telegram API"""
    players = player.create_player_objects(*json_readers.get_player_data_and_player_tables())
    message = "".join([x.generate_telegram_string() for x in players])
    bot_chat_id = update.effective_chat.id
    text = f"Update {datetime.today().strftime('%d.%m.%Y')}\n\n" \
           f"{message}"
    json_readers.update_players_scores(players) if len(players) > 0 else None
    return bot.sendMessage(bot_chat_id, text)


def get_inline_keyboard():
    keyboard = [[
        KeyboardButton("Score"),
        KeyboardButton("Fixtures"),
    ]]
    reply_markup = telegram.ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True, selective=True)
    return reply_markup


def generate_fixture_keyboard_markup(fixtures_list: List[fixtures.Fixture], update: telegram.Update, date_to_filter: datetime) -> telegram.replykeyboardmarkup:
    fixtures_list = select_fixtures(fixtures_list, date_to_filter)
    keyboard = []
    user_id = update.message.from_user["id"]
    #print(user_id)
    username = json_readers.get_player_name_by_id(update.message.from_user["id"])
    for fixture in fixtures_list:
        keyboard.append(
            [KeyboardButton(f"{fixture.home_team}⚽️") if fixture.predictions_dict[username] == '1' else KeyboardButton(fixture.home_team),
             KeyboardButton(f"X⚽️\n{fixture.id}") if fixture.predictions_dict[username] == 'X' else KeyboardButton(f"X\n{fixture.id}"),
             KeyboardButton(f"{fixture.away_team}⚽️") if fixture.predictions_dict[username] == '2' else KeyboardButton(fixture.away_team)])
    keyboard.insert(0, [KeyboardButton(f"Exit matches of {date_to_filter.strftime('%d.%m.%Y')}")])
    keyboard.append([KeyboardButton("Tomorrow")])
    reply_markup = telegram.ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False, selective=True)
    return reply_markup
