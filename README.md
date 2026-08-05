wallasearch
===========

Quick project for `Python3` to search for products in Wallapop, save them in pickle files and keep searching every X seconds (60 by default) to monitor for new products. It will warn you when a new product is found with a desktop notification. If you search for `a` it will create a file `a.pickle` with the results, so when you search again it will only show new results.

Works on Windows, macOS, and Linux.

### Setup

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
```

Activate it:
- **macOS/Linux:** `source .venv/bin/activate`
- **Windows:** `.venv\Scripts\activate`

Then install:
```bash
pip install -r requirements.txt
```

### Usage

```
python wallasearch.py

################################################
# Author:   Sergio Ruiz                        #
# Github:   @serginator                        #
################################################
USAGE: python3 wallasearch.py -s <terms_to_search>

OPTIONS:
  -h, --help
  -s, --search <terms> (if more than one word, use quotes)
  -t, --time <time> (default 60, in seconds)
      --country <country_code> (default ES)
      --postal-code <postal_code> (resolve location via postal code, otherwise uses geo-IP)
      --telegram (send Telegram notification)
      --notify (send desktop notification)
```

Example:

```
~/wallasearch ᐅ python wallasearch.py -s "Lovecraft"
Searching Lovecraft...
New items:

Cthulhu 6 figuras de resina - 15.0
Juego de LOVECRAFT - 25.0
Lovecraft  - 5.0
...

Searching Lovecraft...
```

### Config

In the script file there are two constants that you can modify:

```python
LOOP_TIME = 60  # seconds between executions by default
COUNTRY_CODE = 'ES'  # country code to search by default
```

### Notifying through desktop

Add `--notify` to the command line and it will send a native desktop notification (works on Windows, macOS, and Linux via `plyer`).

### Notifying through Telegram

Add `--telegram` to the command line and it will send a notification to your Telegram.

You need to create a bot (@BotFather), get its token and your internal id (@RawDataBot), then add them to the `.env` file:

```
TELEGRAM_BOT_TOKEN="1234567890:XXX"
TELEGRAM_CHAT_ID="1234567"
```

### Running on Heroku

> **Note:** Heroku removed their free tier in Nov 2022. The cheapest option is an Eco dyno (~$5/month).

The `Procfile` is already configured to run the script as a worker with Telegram notifications (no desktop on a server). All configuration goes through Heroku config vars instead of a `.env` file.

**1. Create the app and set config vars:**

```bash
heroku create
heroku config:set WHAT_TO_SEARCH="Lovecraft"
heroku config:set TELEGRAM_BOT_TOKEN="1234567890:XXX"
heroku config:set TELEGRAM_CHAT_ID="1234567"
heroku config:set POSTAL_CODE="28012"
```

Geo-IP on Heroku's servers resolves to a US datacenter, so `POSTAL_CODE` is important to get results near you.

**2. Deploy:**

```bash
git push heroku master
```

**3. Start the worker:**

```bash
heroku ps:scale worker=1
```

**4. Check logs:**

```bash
heroku logs --tail
```

To stop it: `heroku ps:scale worker=0`

### Adding search term in .env

You can add the term to search in the `.env` file to avoid typing it every time:

```
WHAT_TO_SEARCH="Lovecraft"
```
