import datetime
import json
import pprint
from typing import List
import jsonpickle
import requests
import bs4
import lxml
import ujson

import json_readers


class Fixture():
    def __init__(self, fixture_string: str):
        self.home_team: str = ""
        self.away_team: str = ""
        self.match_datetime: datetime.datetime = None
        self.predictions_dict = { x:"" for x in json_readers.get_player_data_and_player_tables()[0]}
        self.result = ""
        self.id: str = ""
        self.parse_fixture_string(fixture_string)

    def __eq__(self, other) -> bool:
        if type(other) == Fixture.__class__:
            return False
        if self.id == other.id:
            return True
        else:
            return False

    def parse_fixture_string(self, string: str) -> None:
        tokens = string.split("  ")
        tokens = [x.strip() for x in tokens]
        self.home_team = tokens[0]
        # If match is live or finished, tokens[1] and tokens [3] are the score.
        if tokens[1].isnumeric():
            self.result = tokens[1] + ":" + tokens[3]
            self.away_team = tokens[2]
            # If live instead of datetime of match, there is a "X'" string where X is int
            if "'" in tokens[4]: # Live
                now = datetime.datetime.today()
                self.match_datetime = datetime.datetime(now.year, now.month, now.day, 0, 0)
            else: # Finished
                if "Today" in tokens[4]:
                    now = datetime.datetime.today()
                    self.match_datetime = datetime.datetime(now.year, now.month, now.day, 0, 0)
                elif "Yesterday" in tokens[4]:
                    now = datetime.datetime.today() - datetime.timedelta(days=1)
                    self.match_datetime = datetime.datetime(now.year, now.month, now.day, 0, 0)
                elif "Half time" in tokens[4]:
                    now = datetime.datetime.today() - datetime.timedelta(days=1)
                    self.match_datetime = datetime.datetime(now.year, now.month, now.day, 0, 0)
                else:
                    self.match_datetime = datetime.datetime.strptime(tokens[4], "%d/%m/%Y")
            self.id = self.home_team[:2] + self.away_team[:2] + str(self.match_datetime.day) + str(self.match_datetime.month)
            return
        self.away_team = tokens[1]
        if len(tokens) == 3: # fixture is today
            now = datetime.datetime.today()
            if not tokens[2] == "Postponed":
                self.match_datetime = now.strftime("%d/%m/%Y") + ' ' + tokens[2]  # to str
                self.match_datetime = datetime.datetime.strptime(self.match_datetime, "%d/%m/%Y %H:%M")  # to datetime
            else:
                self.match_datetime = datetime.datetime(1, 1, 1)
        elif len(tokens) == 4: # fixture is tomorrow or in the future
            if tokens[2] == "Tomorrow": # tomorrow
                now = datetime.datetime.today()
                tomorrow = datetime.datetime.today() + datetime.timedelta(days=1)
                self.match_datetime = tomorrow.strftime("%d/%m/%Y") + ' ' + tokens[3]  # to str
                self.match_datetime = datetime.datetime.strptime(self.match_datetime, "%d/%m/%Y %H:%M")  # to datetime
            else:
                # TODO: check if zeropadded dates work correctly.
                self.match_datetime = datetime.datetime.strptime(tokens[2] + tokens[3], "%d/%m/%Y%H:%M")
        self.id = self.home_team[:2] + self.away_team[:2] + str(self.match_datetime.day) + str(self.match_datetime.month)

    def get_bet_string(self, user_id: int) -> str:
        user_name = json_readers.get_player_name_by_id(user_id)
        return f"{self.home_team} vs {self.away_team} {self.predictions_dict[user_name]} for {user_name}"
    def __repr__(self) -> str:
        return f"Home: {self.home_team}, Away: {self.away_team}," \
               + f" Date: {self.match_datetime.strftime('%d.%m.%Y %H:%M')}, Result: {self.result}, Id: {self.id}"

    def __str__(self) -> str:
        return f"Home: {self.home_team}\nAway: {self.away_team}\n" \
               + f"Date: {self.match_datetime.strftime('%d.%m.%Y %H:%M')}\nResult: {self.result}\nId: {self.id}"
    def __hash__(self):
        return hash(repr(self))
def sort_key(fixture: Fixture):
    return fixture.match_datetime

def get_fixtures() -> List[Fixture]:
    """Get fixtures"""
    response = requests.get(url=f"https://onefootball.com/en/competition/premier-league-9/fixtures")
    soup = bs4.BeautifulSoup(response.content, 'lxml')
    new_fixtures = soup.findAll("li", class_="simple-match-cards-list__match-card")
    new_fixtures = [x.text.strip() for x in new_fixtures]
    new_fixtures = [Fixture(x) for x in new_fixtures]
    old_fixtures = load_fixtures()
    for old_fix in old_fixtures:
        if old_fix in new_fixtures:
            new_fixtures.remove(old_fix)
    fixtures = list(set(new_fixtures + old_fixtures))
    fixtures.sort(key=sort_key)
    return fixtures

def write_fixtures(fixtures) -> bool:
    """Tries to write fixtures to fixtures.json"""
    try:
        with open("fixtures.json", "w+", encoding="utf8") as file:
            jsonpickle.set_preferred_backend('json')
            jsonpickle.set_encoder_options('json', ensure_ascii=False, sort_keys=True, indent=4)
            file.write(jsonpickle.dumps(fixtures))
    except (IOError, FileNotFoundError, ujson.JSONDecodeError):
        return False


def load_fixtures() -> List[Fixture]:
    """Tries to load fixtures from fixtures.json"""
    try:
        with open("fixtures.json", "r+", encoding="utf8") as file:
            jsonpickle.set_preferred_backend('json')
            jsonpickle.set_decoder_options('json')
            old_fixtures = jsonpickle.loads(file.read())
            return old_fixtures if old_fixtures is not None else []
    except (IOError, FileNotFoundError, ujson.JSONDecodeError):
        return []
