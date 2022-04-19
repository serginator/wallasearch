#!/usr/local/bin/python3
import time
import pickle
import os
import requests
import sys
import getopt

# To load .env file
from dotenv import load_dotenv

def usage():
    print('');
    print('################################################');
    print('# Author:   Sergio Ruiz                        #');
    print('# Github:   @serginator                        #');
    print('################################################');
    print('USAGE: python3 wallasearch.py -s <terms_to_search>');
    print('');
    print('OPTIONS:');
    print('  -h, --help');
    print('  -s, --search <terms> (if more than one word, use quotes)');
    print('  -t, --time <time> (default 60, in seconds)');
    print('      --city <city> (default Madrid)');
    print('      --country <country_code> (default ES)');
    print('      --telegram (send Telegram notification)');
    print('      --osx (send OSX notification)');
    print('');


def send_telegram_notification(message):
    try:
        TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN');
        TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID');
    except:
        print('Error loading .env file');
        os._exit(1);

    try:
        print('Sending Telegram notification...');
        url = "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}".format(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)
        response = requests.get(url)
    except:
        print('Error sending Telegram notification');
        os._exit(1);

def send_osx_notification(message):
    try:
        print('Sending OSX notification...');
        title = 'New items in Wallapop';
        msg = message;
        command = f'''
        osascript -e 'display notification "{msg}" with title "{title}"'
        '''
        os.system(command);
    except:
        print('Error sending OSX notification');
        os._exit(1);

def main():

    # default
    LOOP_TIME = 60; # seconds between executions by default
    USER_CITY = 'Madrid'; # city to search by default
    COUNTRY_CODE = 'ES'; # country code to search by default
    TELEGRAM_NOTIFICATION = False; # don't send Telegram notification by default
    OSX_NOTIFICATION = False; # don't send OSX notification by default
    WHAT_TO_SEARCH = None; # what to search by default

    load_dotenv();

    try:
        opts, _ = getopt.getopt(sys.argv[1:], 'hs:t:', ['help', 'search=', 'time=', 'city=', 'country=', 'telegram', 'osx']);
    except getopt.GetoptError:
        usage();
        sys.exit(2);
    if (len(opts) == 0):
        usage();
        os._exit(0); # sys.exit(0) doesn't works :S

    try:
        # get params from command line
        for opt, arg in opts:
            if opt in ('-h', '--help'):
                usage();
                os._exit(0); # sys.exit(0) doesn't works :S
            elif opt in ('-s', '--search'):
                WHAT_TO_SEARCH = arg.replace(' ', '+');
                PICKLE_FILE_NAME = arg.replace(' ', '_') + '.pickle';
            elif opt in ('-t', '--time'):
                TIME = arg;
            elif opt == '--city':
                USER_CITY = arg;
            elif opt == '--country':
                COUNTRY_CODE = arg;
            elif opt == '--telegram':
                TELEGRAM_NOTIFICATION = True;
            elif opt == '--osx':
                OSX_NOTIFICATION = True;

        if (WHAT_TO_SEARCH == None):
            WHAT_TO_SEARCH=os.getenv('WHAT_TO_SEARCH').replace(' ', '+');
            PICKLE_FILE_NAME = os.getenv('WHAT_TO_SEARCH').replace(' ', '_') + '.pickle';


        URL = 'https://api.wallapop.com/api/v3/general/search?' \
            + 'keywords=' + WHAT_TO_SEARCH + '&start=0' \
            + '&user_city=' + USER_CITY + '&country_code=' + COUNTRY_CODE \
            + '&items_count=0&density_type=20&filters_source=quick_filters&order_by=closest';
    except Exception as e:
            print(e);
            print('Error retrieving params for wallasearch');
            os._exit(2);

    print('Searching ' + WHAT_TO_SEARCH + '...');

    while True:
        start_time = time.time();
        try:
            step = 1;
            keep_going = True;
            full_data = [];

            while keep_going:
                response = requests.get(URL + '&step=' + str(step));
                data = response.json()['search_objects'];
                if len(data) == 0 and len(full_data) > 0:
                    keep_going = False;
                else:
                    step += 1;
                    full_data += data;

            if (len(full_data) > 0):
                new_cards = [];
                for e in full_data:
                    id = e['id'];
                    title = e['title'];
                    sold = e['flags']['sold'];
                    reserved = e['flags']['reserved'];
                    price = e['price'];
                    if (not reserved and not sold):
                        new_cards.append({'id': id, 'title': title, 'price': price});

            new_items = [];
            if os.path.exists(PICKLE_FILE_NAME):
                f = open(PICKLE_FILE_NAME, 'rb');
                d = pickle.load(f);
                f.close();

                for card in new_cards:
                    if card not in d:
                        d.append(card);
                        new_items.append(card);
                if (len(new_items) > 0):
                    f = open(PICKLE_FILE_NAME, 'wb');
                    pickle.dump(d, f);
                    f.close();

            else:
                f = open(PICKLE_FILE_NAME, 'wb');
                pickle.dump(new_cards, f);
                f.close();
                new_items = new_cards;

            if (len(new_items) > 0):
                print('New items found:\n');
                msg = ''
                for item in new_items:
                    print(item['title'] + ' - ' + str(item['price']));
                    msg += item['title'] + ' - ' + str(item['price']) + '\n';
                print('\n');

                if (OSX_NOTIFICATION):
                    send_osx_notification(msg);

                if TELEGRAM_NOTIFICATION:
                    send_telegram_notification(msg);

        except Exception as e:
            print(e);
            print('Error in wallasearch');
            os._exit(2);

        finally:
            # repeat the code
            time.sleep(LOOP_TIME - ((time.time() - start_time) % LOOP_TIME));

if __name__ == '__main__':
    main();
