#!/usr/local/bin/python3
import time
import pickle
import os
import requests
import sys
import getopt

def usage():
    print('');
    print('################################################');
    print('# Author:   Sergio Ruiz                        #');
    print('# Github:   @serginator                        #');
    print('################################################');
    print('USAGE: ./wallasearch.py -s <terms_to_search>');
    print('');
    print('OPTIONS:');
    print('  -h, --help');
    print('  -s, --search <terms> (if more than one word, use quotes)');
    print('  -t, --time <time> (default 60, in seconds)');
    print('      --city <city> (default Madrid)');
    print('      --country <country_code> (default ES)');
    print('');

def main():

    # default
    LOOP_TIME = 60; # seconds between executions by default
    USER_CITY = 'Madrid'; # city to search by default
    COUNTRY_CODE = 'ES'; # country code to search by default

    try:
        opts, _ = getopt.getopt(sys.argv[1:], 'hs:t:', ['help', 'search=', 'time=', 'city=', 'country=']);
    except getopt.GetoptError:
        usage();
        sys.exit(2);
    if (len(opts) == 0):
        usage();
        os._exit(0); # sys.exit(0) doesn't works :S

    while True:
        start_time = time.time();

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

            URL = 'https://api.wallapop.com/api/v3/general/search?' \
              + 'keywords=' + WHAT_TO_SEARCH + '&start=0' \
              + '&user_city=' + USER_CITY + '&country_code=' + COUNTRY_CODE \
              + '&items_count=0&density_type=20&filters_source=quick_filters&order_by=closest';

            step = 1;
            keep_going = True;
            full_data = [];
            print('Searching ' + WHAT_TO_SEARCH + '...');
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
                print('New items:\n');
                msg = ''
                for item in new_items:
                    print(item['title'] + ' - ' + str(item['price']));
                    msg += item['title'] + ' - ' + str(item['price']) + '\n';
                print('\n');
                title = 'New items in Wallapop';
                message = msg;
                command = f'''
                osascript -e 'display notification "{message}" with title "{title}"'
                '''
                os.system(command);

        except Exception as e:
            print(e);
            print('Error in wallasearch');
            os._exit(2);

        finally:
            # repeat the code
            time.sleep(LOOP_TIME - ((time.time() - start_time) % LOOP_TIME));

if __name__ == '__main__':
    main();
