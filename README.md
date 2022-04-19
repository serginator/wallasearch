wallasearch
===========

Quick proyect for OSX in `Python3` to search for products in Wallapop, save them in pickle files and keep searching every X seconds (60 by default) to monitorize for new products. It will warn you when a new product is found with a notification in the system. If you find the text `a` it will create a file `a.pickle` with the results, so when you search for it again it will only show the new results.

### Usage

```python
~/wallasearch (master ✔) ᐅ pip3 install -r requirements.txt
~/wallasearch (master ✔) ᐅ python3 wallasearch.py

################################################
# Author:   Sergio Ruiz                        #
# Github:   @serginator                        #
################################################
USAGE: python3 wallasearch.py -s <terms_to_search>

OPTIONS:
  -h, --help
  -s, --search <terms> (if more than one word, use quotes)
  -t, --time <time> (default 60, in seconds)
      --city <city> (default Madrid)
      --country <country_code> (default ES)
      --telegram (send Telegram notification)
      --osx (send OSX notification)

~/wallasearch ᐅ python3 wallasearch.py -s "Lovecraft"
Searching Lovecraft...
New items:

Cthulhu 6 figuras de resina - 15.0
Juego de LOVECRAFT - 25.0
Lovecraft  - 5.0
...

Searching Lovecraft...
```

### Config

In the script file there are three constants that you can modify

```python
# default
LOOP_TIME = 60; # seconds between executions by default
USER_CITY = "Madrid"; # city to search by default
COUNTRY_CODE = "ES"; # country code to search by default
```

### Notifying through OSX
Just add --osx to the command line and it will send a notification to your OSX desktop.

### Notifying through Telegram
Just add --telegram to the command line and it will send a notification to your Telegram.

You alsoneed to create a bot (@BotFather), get it's token and your internal id (@RawDataBot), and add it to the .env file.
Add them to the .env file.

```
TELEGRAM_BOT_TOKEN="1234567890:XXX"
TELEGRAM_CHAT_ID="1234567"
```
