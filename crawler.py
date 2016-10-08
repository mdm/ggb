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
    return game_ids

def get_ratings(game_id, ratings):
    page = 1
    response = requests.get('http://boardgamegeek.com/xmlapi2/thing?id={}&ratingcomments=1&pagesize=100'.format(game_id))
    soup = BeautifulSoup(response.content, 'lxml')
    num_ratings = 0
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
    return ratings

def serialize(filename, ratings):
    bin_file = open(filename, 'wb')
    for user, games in ratings.items():
        user_bytes = user.encode('utf8')
        bin_file.write(struct.pack('i', len(user_bytes)))
        bin_file.write(user_bytes)
        bin_file.write(struct.pack('i', len(games)))
        for game, rating in games:
            bin_file.write(struct.pack('i', game, rating))
        


game_ids = get_game_ids()
ratings = {}
for game_id in game_ids:
    print(game_id, game_ids[-1])
    ratings = get_ratings(game_id, ratings)
serialize('ratings.bin', ratings)

