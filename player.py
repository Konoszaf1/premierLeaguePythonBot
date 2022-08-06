from typing import List

import web_scrapping


class Player:
    """
    DataClass representing a single player of the game.

    Provides methods for calculating score, max_diff_element, perfect_guess_element
    """

    def __init__(self, name: str, player_table: List[str], num_changes: int, tabledata: List[str], previous_score: int):
        self.name: str = name
        self.player_table: List[str] = player_table
        self.num_changes: int = num_changes
        self.tabledata: List[str] = tabledata
        self.penalty: int = 1
        self.score: int = 0
        self.max_diff_element: str = ""
        self.perfect_guess_element: str = ""
        self.max_diff: int = 0
        self.calculate_score()
        self.score_difference = self.score - previous_score

    def calculate_score(self) -> None:
        """
        Calculate player score according to differences of player_table and tabledata.
        Assigns the respective class attributes.(score, max_diff_element, perfect_guess_element)

        Returns:
            Nothing
        """
        round_diff = 0
        for (a, b) in zip(self.tabledata, self.player_table):

            round_diff = abs(self.tabledata.index(a) - self.player_table.index(a))

            if round_diff == 0:
                self.perfect_guess_element = a

            if round_diff > self.max_diff:
                self.max_diff = round_diff
                self.max_diff_element = a
            self.score += round_diff

        self.score += (self.num_changes * self.penalty)

    def __repr__(self):
        return f"{self.name} has a score of: {self.score}"

    def generate_telegram_string(self) -> str:
        text: str = ""
        text += f"{self.name.upper()}\n" \
                f"Score: {self.score}({'+'+str(self.score_difference) if self.score_difference >=0 else self.score_difference})\n"\
                f"Maximum difference in positions is {self.max_diff} in {self.max_diff_element}.\n" \
                f"+{self.num_changes * self.penalty} point penalty is included.\n\n"
        return text


def create_player_objects(player_data_dict: dict, player_tables_dict: dict) -> List[Player]:
    """Create Player class objects with data from passed dictionaries."""
    if player_data_dict is None or player_tables_dict is None:
        return []
    players_list: List[Player] = []
    for new_player in player_tables_dict.keys():
        players_list.append(
            Player(new_player, player_tables_dict[new_player], player_data_dict[new_player]["changes"],
                   web_scrapping.web_scrape_table(), player_data_dict[new_player]["score"]))
    return players_list

