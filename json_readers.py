"""Utility functions that handle writing and reading to and from json files."""
import json
import traceback
from typing import Tuple, List

from player import Player


def read_json_tables() -> Tuple[dict, dict]:
    """Attempts to open 'player_tables.json' and 'player_data.json' and returns them as a tuple of dicts."""
    with open('player_tables.json') as file:
        player_tables_dict: dict = json.load(file)

    with open('player_data.json') as file:
        player_data_dict: dict = json.load(file)
        if len(player_data_dict.keys()) < len(player_tables_dict.keys()):
            for added_player in [x for x in player_tables_dict.keys() if x not in player_data_dict.keys()]:
                player_data_dict[added_player] = {"score": 0, "changes": 0, "user_id": 0}

    return player_data_dict, player_tables_dict


def get_player_data_and_player_tables() -> Tuple[dict, dict]:
    """Read json files"""
    try:
        player_data, player_tables = read_json_tables()
    except (IOError, FileNotFoundError, json.decoder.JSONDecodeError):
        print(traceback.format_exc())
        player_data = player_tables = None
    return player_data, player_tables


def get_player_name_by_id(user_id: object) -> str:
    """Get player_name according to passed telegram user_id from player_data.json"""
    try:
        with open('player_data.json') as file:
            player_tables_dict: dict = json.load(file)
        for index, player in enumerate(player_tables_dict):
            if player_tables_dict[player]["user_id"] == user_id:
                return str(list(player_tables_dict.keys())[index])
    except (IOError, FileNotFoundError, json.decoder.JSONDecodeError):
        pass


def update_players_scores(players_list: List[Player]) -> None:
    """Opens 'player_data.json' and attempts to update the key values with calculated data."""
    with open('player_data.json', 'w') as outfile:
        temp_dict = {}
        for player in players_list:
            temp_dict.update(
                {player.name: {"score": player.score, "changes": player.num_changes, "user_id": player.user_id}})
        json.dump(temp_dict, outfile, sort_keys=True, indent=4)


def get_key(key: str):
    """Opens 'keys.json' and attempts to fetch the passed key."""
    try:
        with open('keys.json', 'r+') as read_file:
            temp_dict = json.load(read_file)
        return temp_dict[key]
    except (IOError, FileNotFoundError, json.decoder.JSONDecodeError):
        pass
