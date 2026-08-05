#!/usr/local/bin/python3
import time
import pickle
import os
import uuid
import requests
import sys
import getopt

from dotenv import load_dotenv

API_HEADERS = {
    'deviceos': '0',
    'x-appversion': '825350',
    'x-deviceos': '0',
    'x-deviceid': str(uuid.uuid4()),
    'mpid': str(-(uuid.uuid4().int >> 65)),
}
API_HEADERS['trackinguserid'] = API_HEADERS['mpid']

def geocode(postal_code, country_code):
    res = requests.get(
        'https://nominatim.openstreetmap.org/search',
        params={'postalcode': postal_code, 'countrycodes': country_code.lower(), 'format': 'json', 'limit': 1},
        headers={'User-Agent': 'wallasearch/1.0'},
    ).json()
    if not res:
        raise ValueError(f'Postal code {postal_code} not found for country {country_code}')
    return res[0]['lat'], res[0]['lon']


def fetch_items(keywords, country_code, lat=None, lon=None):
    comp_url = (
        'https://api.wallapop.com/api/v3/search/components'
        f'?keywords={keywords}&order_by=newest&source=deep_link'
    )
    comp_data = requests.get(
        comp_url, headers={**API_HEADERS, 'Accept': 'application/json; sequence=v2'}
    ).json()

    organic = next(c for c in comp_data['components'] if c.get('id') == 'organic_search_results')
    params = {**organic['type_data']['query_params'], 'search_country': country_code}
    if lat and lon:
        params['latitude'], params['longitude'] = lat, lon

    items = requests.get(
        'https://api.wallapop.com/api/v3/search/section',
        params=params,
        headers={**API_HEADERS, 'Accept': 'application/json, text/plain, */*'},
    ).json()['data']['section']['items']

    return [
        {'id': e['id'], 'title': e['title'], 'price': e['price']['amount']}
        for e in items
        if not e['reserved']['flag']
    ]


def send_telegram_notification(message):
    try:
        TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    except:
        print('Error loading .env file')
        os._exit(1)

    try:
        print('Sending Telegram notification...')
        url = "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}".format(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)
        requests.get(url)
    except:
        print('Error sending Telegram notification')
        os._exit(1)

def send_desktop_notification(message):
    try:
        import platform
        print('Sending desktop notification...')
        if platform.system() == 'Darwin':
            safe = message.replace('"', "'")
            os.system(f'osascript -e \'display notification "{safe}" with title "New items in Wallapop"\'')
        else:
            from plyer import notification
            notification.notify(title='New items in Wallapop', message=message, timeout=10)
    except:
        print('Error sending desktop notification')
        os._exit(1)

def usage():
    print('')
    print('################################################')
    print('# Author:   Sergio Ruiz                        #')
    print('# Github:   @serginator                        #')
    print('################################################')
    print('USAGE: python3 wallasearch.py -s <terms_to_search>')
    print('')
    print('OPTIONS:')
    print('  -h, --help')
    print('  -s, --search <terms> (if more than one word, use quotes)')
    print('  -t, --time <time> (default 60, in seconds)')
    print('      --country <country_code> (default ES)')
    print('      --postal-code <postal_code> (resolve location via postal code, otherwise uses geo-IP)')
    print('      --telegram (send Telegram notification)')
    print('      --notify (send desktop notification)')
    print('')


def main():
    LOOP_TIME = 60
    COUNTRY_CODE = 'ES'
    POSTAL_CODE = None
    TELEGRAM_NOTIFICATION = False
    DESKTOP_NOTIFICATION = False
    WHAT_TO_SEARCH = None

    load_dotenv()

    try:
        opts, _ = getopt.getopt(sys.argv[1:], 'hs:t:', ['help', 'search=', 'time=', 'country=', 'postal-code=', 'telegram', 'notify'])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    if len(opts) == 0:
        usage()
        os._exit(0)

    try:
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                usage()
                os._exit(0)
            elif opt in ('-s', '--search'):
                WHAT_TO_SEARCH = arg.replace(' ', '+')
                PICKLE_FILE_NAME = arg.replace(' ', '_') + '.pickle'
            elif opt in ('-t', '--time'):
                LOOP_TIME = int(arg)
            elif opt == '--country':
                COUNTRY_CODE = arg
            elif opt == '--postal-code':
                POSTAL_CODE = arg
            elif opt == '--telegram':
                TELEGRAM_NOTIFICATION = True
            elif opt == '--notify':
                DESKTOP_NOTIFICATION = True

        if WHAT_TO_SEARCH is None:
            WHAT_TO_SEARCH = os.getenv('WHAT_TO_SEARCH').replace(' ', '+')
            PICKLE_FILE_NAME = os.getenv('WHAT_TO_SEARCH').replace(' ', '_') + '.pickle'

        if POSTAL_CODE is None:
            POSTAL_CODE = os.getenv('POSTAL_CODE')

    except Exception as e:
        print(e)
        print('Error retrieving params for wallasearch')
        os._exit(2)

    lat, lon = geocode(POSTAL_CODE, COUNTRY_CODE) if POSTAL_CODE else (None, None)

    print('Searching ' + WHAT_TO_SEARCH + '...')

    while True:
        start_time = time.time()
        try:
            new_cards = fetch_items(WHAT_TO_SEARCH, COUNTRY_CODE, lat, lon)

            new_items = []
            if os.path.exists(PICKLE_FILE_NAME):
                with open(PICKLE_FILE_NAME, 'rb') as f:
                    d = pickle.load(f)

                for card in new_cards:
                    if card not in d:
                        d.append(card)
                        new_items.append(card)
                if new_items:
                    with open(PICKLE_FILE_NAME, 'wb') as f:
                        pickle.dump(d, f)
            else:
                with open(PICKLE_FILE_NAME, 'wb') as f:
                    pickle.dump(new_cards, f)
                new_items = new_cards

            if new_items:
                print('New items found:\n')
                msg = ''
                for item in new_items:
                    print(item['title'] + ' - ' + str(item['price']))
                    msg += item['title'] + ' - ' + str(item['price']) + '\n'
                print('')

                if DESKTOP_NOTIFICATION:
                    send_desktop_notification(msg)

                if TELEGRAM_NOTIFICATION:
                    send_telegram_notification(msg)

        except Exception as e:
            print(e)
            print('Error in wallasearch')
            os._exit(2)

        finally:
            time.sleep(LOOP_TIME - ((time.time() - start_time) % LOOP_TIME))

if __name__ == '__main__':
    main()
