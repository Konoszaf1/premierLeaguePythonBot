""" File consists of helper functions that facilitate communication with telegram"""
from typing import List

import fixtures
import telegram
from telegram import ext, ReplyKeyboardMarkup, KeyboardButton, Message
from datetime import datetime, timedelta

import json_readers
import player


def handle_received_message(update: telegram.Update, context: ext.CallbackContext) -> None:
    """Handle message and respond according to included text."""
    received_text = update.message.text
    bot = context.bot
    if received_text.lower() == "start":  # Start Bot Session send menu including "Fixtures" and "Score"
        update.message.reply_text(text="Starting Bot...", reply_markup=get_inline_keyboard())
        bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
    elif "exit" in received_text.lower():  # Exit Bot Session send menu including "Fixtures" and "Score"
        previous_message = update.message.reply_to_message
        message_to_be_deleted = update.message.reply_text(text="Dummy reply message to end session",
                                                          reply_markup=telegram.ReplyKeyboardRemove(selective=True))
        bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        bot.delete_message(chat_id=message_to_be_deleted.chat_id, message_id=message_to_be_deleted.message_id)
        bot.delete_message(chat_id=previous_message.chat_id, message_id=previous_message.message_id)
    elif received_text.lower() == 'score':  # Send current prediction score as a message
        previous_message = update.message.reply_to_message
        telegram_bot_send_score(bot, update=update)
        bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        bot.delete_message(chat_id=previous_message.chat_id, message_id=previous_message.message_id)
    elif received_text.lower() == "fixtures":  # Send Fixtures Menu and allow players to bet by clicking on button
        previous_message = update.message.reply_to_message
        fixtures_list = fixtures.get_fixtures()
        update.message.reply_text(text=f"Fixtures for {datetime.today().strftime('%d.%m.%Y')}",
                                  reply_markup=generate_fixture_keyboard_markup(fixtures_list, update,
                                                                                date_to_filter=datetime.today()))
        bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        bot.delete_message(chat_id=previous_message.chat_id, message_id=previous_message.message_id)
        fixtures.write_fixtures(fixtures_list)
    elif received_text.lower() == "next day":
        fixtures_list = fixtures.load_fixtures()
        previous_message = update.message.reply_to_message
        previous_date = datetime.strptime(previous_message.text[previous_message.text.rindex(" "):].strip(), '%d.%m.%Y')
        next_date = previous_date + timedelta(days=1)
        update.message.reply_text(text=f"Fixtures for {next_date.strftime('%d.%m.%Y')}",
                                  reply_markup=generate_fixture_keyboard_markup(fixtures_list, update, next_date))
        bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        bot.delete_message(chat_id=previous_message.chat_id, message_id=previous_message.message_id)
    else:
        fixtures_list = fixtures.load_fixtures()
        previous_message = None
        if "for" in received_text:
            previous_message = update.message.reply_to_message
        if ((received_text in ([x.home_team for x in fixtures_list] + [x.away_team for x in fixtures_list]))
                or ('X' in received_text and received_text[received_text.index('\n') + 1:] in [x.id for x in
                                                                                               fixtures_list])):
            previous_message = update.message.reply_to_message
            previous_date = datetime.strptime(previous_message.text[previous_message.text.rindex(" "):].strip(),
                                              '%d.%m.%Y')
            temp_fixtures_list = select_fixtures(fixtures_list, previous_date)
            player_string = json_readers.get_player_name_by_id(update.message.from_user["id"])
            if 'x' not in received_text.lower() and '\n' not in received_text.lower():
                bet_fixture = \
                    [x for x in temp_fixtures_list if x.home_team == received_text or x.away_team == received_text][0]
                if bet_fixture.predictions_dict[player_string] == "":
                    bet_fixture.predictions_dict[player_string] = '1' if received_text in [x.home_team for x in
                                                                                           temp_fixtures_list] else '2'
            else:
                match_id = received_text[received_text.index('\n') + 1:]
                bet_fixture = [x for x in temp_fixtures_list if x.id == match_id][0]
                if bet_fixture.predictions_dict[player_string] == "":
                    bet_fixture.predictions_dict[player_string] = 'X'
            fixtures.write_fixtures(fixtures_list)
            update.message.reply_text(text=f"Fixtures for {previous_date.strftime('%d.%m.%Y')}",
                                      reply_markup=generate_fixture_keyboard_markup(fixtures_list, update,
                                                                                    previous_date))
        bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)
        if previous_message is not None:
            bot.delete_message(chat_id=previous_message.chat_id, message_id=previous_message.message_id)


def select_fixtures(fixtures_list, filter_datetime: datetime) -> List[fixtures.Fixture]:
    """Returns fixtures from fixtures_list that are on the same day of the passed datetime_filter"""

    def check_same_day(test: fixtures.Fixture):
        """True if fixture is on the same day, else false."""
        if filter_datetime.day == test.match_datetime.day \
                and filter_datetime.month == test.match_datetime.month \
                and filter_datetime.year == test.match_datetime.year \
                and filter_datetime.hour < test.match_datetime.hour \
                and filter_datetime.minute < test.match_datetime.minute:
            return True
        return False

    fixtures_list = [x for x in fixtures_list if check_same_day(x)]
    fixtures_list.sort(key=fixtures.sort_key)
    return fixtures_list


def telegram_bot_send_score(bot: telegram.Bot, update: telegram.Update = None, chat_id=None) -> Message:
    """Send score via Telegram API"""
    players = player.create_player_objects(*json_readers.get_player_data_and_player_tables())
    message = "".join([x.generate_telegram_string() for x in players])
    bot_chat_id = update.effective_chat.id if update is not None else chat_id
    text = f"Update {datetime.today().strftime('%d.%m.%Y')}\n\n" \
           f"{message}"
    json_readers.update_players_scores(players) if len(players) > 0 else None
    return bot.sendMessage(bot_chat_id, text)


def get_inline_keyboard() -> ReplyKeyboardMarkup:
    """Returns a keyboard Markup containing two buttons: Score and Fixtures"""
    keyboard = [[
        KeyboardButton("Score"),
        KeyboardButton("Fixtures"),
    ]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True, selective=True)
    return reply_markup


def generate_fixture_keyboard_markup(fixtures_list: List[fixtures.Fixture], update: telegram.Update,
                                     date_to_filter: datetime) -> telegram.replykeyboardmarkup:
    """Iterate through passed fixtures and generate a ReplyKeyboardMarkup according to them and player bets."""
    fixtures_list = select_fixtures(fixtures_list, date_to_filter)
    keyboard = []
    # print(update.message.from_user["id"])
    username = json_readers.get_player_name_by_id(update.message.from_user["id"])
    for fixture in fixtures_list:
        keyboard.append(
            [KeyboardButton(f"{fixture.home_team}⚽️") if fixture.predictions_dict[username] == '1'
             else KeyboardButton(fixture.home_team),
             KeyboardButton(f"X⚽️\n{fixture.id}") if fixture.predictions_dict[username] == 'X'
             else KeyboardButton(f"X\n{fixture.id}"),
             KeyboardButton(f"{fixture.away_team}⚽️") if fixture.predictions_dict[username] == '2'
             else KeyboardButton(fixture.away_team)])
    keyboard.insert(0, [KeyboardButton(f"Exit matches of {date_to_filter.strftime('%d.%m.%Y')}")])
    keyboard.append([KeyboardButton("Next day")])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False, selective=True)
    return reply_markup
