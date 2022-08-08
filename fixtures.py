"""Provides a dataclass for fixtures along with methods for fetching them and parsing them into objects."""
from typing import List
import jsonpickle
import requests
import bs4
from ujson import JSONDecodeError
from datetime import datetime, timedelta
import json_readers


class Fixture:
    """Simple data class created from parsing the fetched string from the web."""
    def __init__(self, fixture_string: str):
        self.home_team: str = ""
        self.away_team: str = ""
        self.match_datetime: datetime = None
        self.predictions_dict = {x:"" for x in json_readers.get_player_data_and_player_tables()[0]}
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

    def parse_fixture_string(self, string) -> None:
        """Parse the string and assign values to the class' fields according to the passed tokens."""
        tokens = string.split("  ")
        tokens = [x.strip() for x in tokens]
        for index, token in enumerate(tokens):
            if index == 0:  # First token is always home team
                self.home_team = token
            elif index == 1 and token.isnumeric():  # Second token can be either home team goals
                self.result = f"{token}:{tokens[3]}"  # in this case 4th token is away team goals
                self.away_team = tokens[2]  # and 3rd token is away team
            elif index == 1 and not token.isnumeric():  # or away team
                self.away_team = token
            elif index == 2 and ":" in token:  # 3rd token is XX:XX and match is today
                now = datetime.today()
                self.match_datetime = now.strftime("%d/%m/%Y") + token.strip()  # to str
                self.match_datetime = datetime.strptime(self.match_datetime, "%d/%m/%Y%H:%M")
            elif index == 2 and "Postponed" in token:  # Match is postponed
                self.match_datetime = datetime(1, 1, 1)
            elif index == 2 and "/" in token:  # Token is a datetime
                self.match_datetime = datetime.strptime(token.strip() + " " + tokens[3].strip(), "%d/%m/%Y %H:%M")
            elif index == 2 and "Tomorrow" in token:  # Token says "Tomorrow" instead of a datetime
                now = datetime.today() + timedelta(days=1)
                self.match_datetime = now.strftime("%d/%m/%Y") + tokens[3].strip()  # to str
                self.match_datetime = datetime.strptime(self.match_datetime, "%d/%m/%Y%H:%M")
            elif index == 4 and ("'" in token or "Half time" in token or "Today" in token):  # Match is live
                now = datetime.today()
                self.match_datetime = now.strftime("%d/%m/%Y")
                self.match_datetime = datetime.strptime(self.match_datetime, "%d/%m/%Y")
            elif index == 4 and "/" in token:  # Token is a datetime
                self.match_datetime = datetime.strptime(token, "%d/%m/%Y")
            elif index == 4 and "Yesterday" in token:  # Match finished yesterday
                now = datetime.today() + timedelta(days=1)
                self.match_datetime = now.strftime("%d/%m/%Y")
                self.match_datetime = datetime.strptime(self.match_datetime, "%d/%m/%Y")
        self.id = self.home_team[:2] + self.away_team[:2] + str(self.match_datetime.day) + str(self.match_datetime.month)

    def get_bet_string(self, user_id: int) -> str:
        """Visual representation of the bet of a user for messaging purposes."""
        user_name = json_readers.get_player_name_by_id(user_id)
        return f"{self.home_team} vs {self.away_team} {self.predictions_dict[user_name]} for {user_name}"

    def __repr__(self) -> str:
        """Provides string representation of class for stdout purposes."""
        return f"Home: {self.home_team}, Away: {self.away_team}," \
               + f" Date: {self.match_datetime.strftime('%d.%m.%Y %H:%M')}, Result: {self.result}, Id: {self.id}"

    def __str__(self) -> str:
        return f"Home: {self.home_team}\nAway: {self.away_team}\n" \
               + f"Date: {self.match_datetime.strftime('%d.%m.%Y %H:%M')}\nResult: {self.result}\nId: {self.id}"

    def __hash__(self) -> int:
        """Override implementation of hash to make class hashable"""
        return hash(repr(self))


def sort_key(fixture: Fixture):
    """Used to sort fixtures according to their datetime."""
    return fixture.match_datetime


def get_fixtures() -> List[Fixture]:
    """Get fixtures"""
    response = requests.get(url=f"https://onefootball.com/en/competition/premier-league-9/fixtures")
    soup = bs4.BeautifulSoup(response.content, 'lxml')
    new_fixtures = soup.findAll("li", class_="simple-match-cards-list__match-card")
    new_fixtures = [x.text.strip() for x in new_fixtures]
    new_fixtures = [Fixture(x) for x in new_fixtures]
    old_fixtures = load_fixtures()
    old_fixtures = sync_old_and_new_fixtures(old_fixtures, new_fixtures)
    for old_fix in old_fixtures:
        if old_fix in new_fixtures:
            new_fixtures.remove(old_fix)
    fixtures = list(set(new_fixtures + old_fixtures))
    fixtures.sort(key=sort_key)
    return fixtures


def sync_old_and_new_fixtures(old_fixtures: List[Fixture], new_fixtures: List[Fixture]):
    """Compares two lists and updates the 'result' field of the old_fixtures with the updated values of new_fixtures."""
    fixtures_that_can_be_updated = []
    for old_fix in old_fixtures:
        if old_fix in new_fixtures:
            fixtures_that_can_be_updated.append(old_fix)
    for fixture in fixtures_that_can_be_updated:
        fixture.result = new_fixtures[new_fixtures.index(fixture)].result
    for fixture in fixtures_that_can_be_updated:
        if fixture in old_fixtures:
            old_fixtures.remove(fixture)
            old_fixtures.append(fixture)
    return old_fixtures


def write_fixtures(fixtures) -> bool:
    """Tries to write fixtures to fixtures.json"""
    try:
        with open("fixtures.json", "w+", encoding="utf8") as file:
            jsonpickle.set_preferred_backend('json')
            jsonpickle.set_encoder_options('json', ensure_ascii=False, sort_keys=True, indent=4)
            file.write(jsonpickle.dumps(fixtures))
    except (IOError, FileNotFoundError, JSONDecodeError):
        return False


def load_fixtures() -> List[Fixture]:
    """Tries to load fixtures from fixtures.json"""
    try:
        with open("fixtures.json", "r+", encoding="utf8") as file:
            jsonpickle.set_preferred_backend('json')
            jsonpickle.set_decoder_options('json')
            old_fixtures = jsonpickle.loads(file.read())
            return old_fixtures if old_fixtures is not None else []
    except (IOError, FileNotFoundError, JSONDecodeError):
        return []
