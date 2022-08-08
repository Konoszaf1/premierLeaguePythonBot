from typing import List

from requests_html import HTMLSession

PREMIER_LEAGUE_TABLE_URL = 'https://www.skysports.com/premier-league-table'


def web_scrape_table() -> List[str]:
    """Scrapes the web using requests_html for the premier league table and returns the name column as is. """
    request = HTMLSession().get(PREMIER_LEAGUE_TABLE_URL)
    table = request.html.find('table')[0]
    tabledata = [[c.text for c in row.find('td')[1:][:-9]] for row in table.find('tr')[1:]]
    return [x for sublist in tabledata for x in sublist]
