import re
import time
import struct

from bs4 import BeautifulSoup
import requests


def get_game_ids():
    game_ids = []
    game_id_regex = re.compile(r'boardgame/([0-9]+)')
    response = requests.get('http://boardgamegeek.com/sitemapindex')
    soup_index = BeautifulSoup(response.content, 'lxml')
    for sitemap_loc in soup_index.find_all('loc'):
        sitemap_url = sitemap_loc.string.strip()
        print(sitemap_url)
        if not sitemap_url.find('geekitems_boardgame_') == -1:
            response = requests.get(sitemap_url)
            soup_geekitems = BeautifulSoup(response.content, 'lxml')
            for game_loc in soup_geekitems.find_all('loc'):
                game_url = game_loc.string.strip()
                print('***', game_url)
                game_id = int(game_id_regex.search(game_url).group(1))
                game_ids.append(game_id)
    game_ids.sort()
    return game_ids

def get_ratings(game_id, ratings):
    num_ratings = 0
    page = 1
    response = requests.get('http://boardgamegeek.com/xmlapi2/thing?id={}&ratingcomments=1&pagesize=100'.format(game_id))
    soup = BeautifulSoup(response.content, 'lxml')
    total_ratings = int(soup.find('comments').get('totalitems'))
    while True:
        #print(page)
        for rating in soup.find_all('comment'):
            ratings.setdefault(rating.get('username'), set()).add((game_id, rating.get('rating')))
            num_ratings += 1
        if num_ratings == total_ratings:
            break
        time.sleep(2)
        page += 1
        response = requests.get('http://boardgamegeek.com/xmlapi2/thing?id={}&ratingcomments=1&page={}&pagesize=100'.format(game_id, page))
        soup = BeautifulSoup(response.content, 'lxml')
        total_ratings = int(soup.find('comments').get('totalitems'))
    return ratings


start = 0
game_ids = get_game_ids()
for game_id in game_ids:
    if game_id > start:
        print(game_id, game_ids[-1])
        ratings = get_ratings(game_id, ratings)

