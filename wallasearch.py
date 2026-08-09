#!/usr/local/bin/python3
import time
import pickle
import os
import uuid
import requests
import sys
import getopt
import urllib.parse

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


def fetch_items(keywords, country_code, lat=None, lon=None, min_price=None, max_price=None):
    comp_url = (
        'https://api.wallapop.com/api/v3/search/components'
        f'?keywords={keywords}&order_by=newest&source=deep_link'
    )
    if min_price is not None:
        comp_url += f'&min_sale_price={min_price}'
    if max_price is not None:
        comp_url += f'&max_sale_price={max_price}'

    comp_data = requests.get(
        comp_url, headers={**API_HEADERS, 'Accept': 'application/json; sequence=v2'}
    ).json()

    organic = next(c for c in comp_data['components'] if c.get('id') == 'organic_search_results')
    params = {**organic['type_data']['query_params'], 'search_country': country_code}
    if lat and lon:
        params['latitude'], params['longitude'] = lat, lon

    if min_price is not None:
        params['min_sale_price'] = min_price
    if max_price is not None:
        params['max_sale_price'] = max_price

    items = requests.get(
        'https://api.wallapop.com/api/v3/search/section',
        params=params,
        headers={**API_HEADERS, 'Accept': 'application/json, text/plain, */*'},
    ).json()['data']['section']['items']

    return [
        {
            'id': e['id'], 
            'title': e['title'], 
            'price': e['price']['amount'],
            'web_slug': e.get('web_slug', '')
        }
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
        encoded_message = urllib.parse.quote(message)
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={encoded_message}&disable_web_page_preview=false"
        requests.get(url)
    except:
        print('Error sending Telegram notification')
        os._exit(1)

def send_desktop_notification(message):
    try:
        import platform
        print('Sending desktop notification...')
        lines = [l for l in message.strip().splitlines() if l]
        
        # Group into items (title+price, url, blank line)
        items = []
        i = 0
        while i < len(lines):
            if i + 1 < len(lines) and lines[i+1].startswith('https://'):
                items.append(f"{lines[i]}\n{lines[i+1]}")
                i += 2
            else:
                items.append(lines[i])
                i += 1
        
        # Show first item with URL, or just count if too many
        if len(items) == 1:
            summary = items[0]
        elif len(items) > 1:
            summary = f"{items[0]}\n\n(+{len(items) - 1} more items)"
        else:
            summary = lines[0] if lines else "New items found"
            
        if platform.system() == 'Darwin':
            safe = summary.replace('"', "'").replace('\\', '')
            os.system(f'osascript -e \'display notification "{safe}" with title "New items in Wallapop" sound name "default"\'')
        else:
            from plyer import notification
            notification.notify(title='New items in Wallapop', message=summary, timeout=10)
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
    print('      --min-price <amount> (minimum price filter)')
    print('      --max-price <amount> (maximum price filter)')
    print('      --telegram (send Telegram notification)')
    print('      --notify (send desktop notification)')
    print('')


def main():
    LOOP_TIME = 60
    COUNTRY_CODE = 'ES'
    POSTAL_CODE = None
    MIN_PRICE = None
    MAX_PRICE = None
    TELEGRAM_NOTIFICATION = False
    DESKTOP_NOTIFICATION = False
    WHAT_TO_SEARCH = None

    load_dotenv()

    try:
        opts, _ = getopt.getopt(sys.argv[1:], 'hs:t:', ['help', 'search=', 'time=', 'country=', 'postal-code=', 'min-price=', 'max-price=', 'telegram', 'notify'])
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
                RAW_SEARCH = arg
            elif opt in ('-t', '--time'):
                LOOP_TIME = int(arg)
            elif opt == '--country':
                COUNTRY_CODE = arg
            elif opt == '--postal-code':
                POSTAL_CODE = arg
            elif opt == '--min-price':
                MIN_PRICE = float(arg)
            elif opt == '--max-price':
                MAX_PRICE = float(arg)
            elif opt == '--telegram':
                TELEGRAM_NOTIFICATION = True
            elif opt == '--notify':
                DESKTOP_NOTIFICATION = True

        if WHAT_TO_SEARCH is None:
            RAW_SEARCH = os.getenv('WHAT_TO_SEARCH')
            WHAT_TO_SEARCH = RAW_SEARCH.replace(' ', '+')

        filename_str = RAW_SEARCH.replace(' ', '_')
        if MIN_PRICE: filename_str += f'_min{MIN_PRICE}'
        if MAX_PRICE: filename_str += f'_max{MAX_PRICE}'
        PICKLE_FILE_NAME = filename_str + '.pickle'

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
            new_cards = fetch_items(WHAT_TO_SEARCH, COUNTRY_CODE, lat, lon, MIN_PRICE, MAX_PRICE)

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
                    slug = item.get('web_slug', '')
                    item_url = f"https://es.wallapop.com/item/{slug}" if slug else "https://es.wallapop.com"
                    
                    line = f"{item['title']} - {item['price']}€\n{item_url}\n"
                    print(line)
                    msg += line + '\n'

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
