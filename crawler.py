import re
from bs4 import BeautifulSoup
import requests

#game_data = open('game_data.bin', 'wb')

game_id_regex = re.compile(r'boardgame/([0-9]+)')
response = requests.get('http://boardgamegeek.com/sitemapindex')
soup_index = BeautifulSoup(response.content, 'lxml')
for sitemap_loc in soup_index.find_all('loc'):
    sitemap_url = sitemap_loc.string.strip()
    if sitemap_url.find('geekitems_boardgame'):
        print(sitemap_url)
        response = requests.get(sitemap_url)
        soup_geekitems = BeautifulSoup(response.content, 'lxml')
        for game_loc in soup_geekitems.find_all('loc'):
            game_url = game_loc.string.strip()
            print(game_url)
            game_id = int(game_id_regex.search(game_url).group(1))
            print(game_id)

