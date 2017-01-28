import re
import time
import json
import sys

from bs4 import BeautifulSoup
import requests

def get_page_with_retries(url):
    backoff_secs = 2
    while True:
        try:
            response = requests.get(url)
            if response.status_code == requests.codes.ok:
                return response.content
            else:
                print('Received a status code', response.status_code)
                if backoff_secs > 1024:
                    response.raise_for_status()
        except KeyboardInterrupt:
            raise
        except:
            if backoff_secs > 1024:
                raise
        print('Backing off for', backoff_secs, 'seconds')
        time.sleep(backoff_secs)
        backoff_secs *= 2



def get_game_ids(last_downloaded):
    game_ids = []
    game_id_regex = re.compile(r'boardgame/([0-9]+)')
    response = get_page_with_retries('http://boardgamegeek.com/sitemapindex')
    soup_index = BeautifulSoup(response, 'lxml')
    for sitemap_loc in soup_index.find_all('loc'):
        sitemap_url = sitemap_loc.string.strip()
        if not sitemap_url.find('geekitems_boardgame_') == -1:
            print(sitemap_url)
            response = get_page_with_retries(sitemap_url)
            soup_geekitems = BeautifulSoup(response, 'lxml')
            for game_loc in soup_geekitems.find_all('loc'):
                game_url = game_loc.string.strip()
                game_id = int(game_id_regex.search(game_url).group(1))
                if game_id > last_downloaded:
                    game_ids.append(game_id)
    return sorted(game_ids)

def get_info(game_id):
    info = {}
    response = get_page_with_retries('http://boardgamegeek.com/xmlapi2/thing?id={}&ratingcomments=1&pagesize=100'.format(game_id))
    soup = BeautifulSoup(response, 'lxml')
    for name in soup.find_all('name'):
        if name.get('type') == 'primary':
            info['name'] = name.get('value')
            break
    info['year'] = int(soup.find('yearpublished').get('value'))
    return info

def get_ratings(game_id, users):
    ratings = {}
    num_ratings = 0 # needed to count duplicate ratings
    page = 1
    response = get_page_with_retries('http://boardgamegeek.com/xmlapi2/thing?id={}&ratingcomments=1&pagesize=100'.format(game_id))
    soup = BeautifulSoup(response, 'lxml')
    total_ratings = int(soup.find('comments').get('totalitems'))
    while True:
        print('  Page', page)
        for rating in soup.find_all('comment'):
            username = rating.get('username')
            value = float(rating.get('rating'))
            if not username in users:
                if users:
                    users[username] = max(users.values()) + 1
                else:
                    users[username] = 1
            ratings[str(users[username])] = value
            num_ratings += 1
        if num_ratings == total_ratings:
            break
        time.sleep(2)
        page += 1
        response = get_page_with_retries('http://boardgamegeek.com/xmlapi2/thing?id={}&ratingcomments=1&page={}&pagesize=100'.format(game_id, page))
        soup = BeautifulSoup(response, 'lxml')
        total_ratings = int(soup.find('comments').get('totalitems'))
    return ratings


with open('games.json', 'r') as games_file:
    games = json.load(games_file)
with open('users.json', 'r') as users_file:
    users = json.load(users_file)
with open('ratings.json', 'r') as ratings_file:
    ratings = json.load(ratings_file)
if len(sys.argv) > 1:
    last_downloaded = int(sys.argv[1])
elif games:
    last_downloaded = max([int(k) for k in games.keys()])
else:
    last_downloaded = 0
game_ids = get_game_ids(last_downloaded)
print('Found', len(game_ids), 'missing games.')
for game_id in game_ids:
    print('Processing game {}...'.format(game_id))
    try:
        game_info = get_info(game_id)
        game_ratings = get_ratings(game_id, users)
        print(len(game_ratings), 'ratings found')
        games[str(game_id)] = game_info
        ratings[str(game_id)] = game_ratings
    except:
        with open('games.json', 'w') as games_file:
            json.dump(games, games_file)
        with open('users.json', 'w') as users_file:
            json.dump(users, users_file)
        with open('ratings.json', 'w') as ratings_file:
            json.dump(ratings, ratings_file)
        raise

