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
      --min-price <amount> (minimum price filter)
      --max-price <amount> (maximum price filter)
      --telegram (send Telegram notification)
      --notify (send desktop notification)
      --once (run a single check and exit, useful for schedulers like GitHub Actions)
```

Examples:

```bash
# Basic search
python wallasearch.py -s "Lovecraft"

# Search with price range
python wallasearch.py -s "iPhone" --min-price 100 --max-price 500

# Search with notifications
python wallasearch.py -s "Lovecraft" --notify --telegram
```

Output:

```
~/wallasearch ᐅ python wallasearch.py -s "Lovecraft"
Searching Lovecraft...
New items found:

Cthulhu 6 figuras de resina - 15.0€
https://es.wallapop.com/item/cthulhu-6-figuras-de-resina

Juego de LOVECRAFT - 25.0€
https://es.wallapop.com/item/juego-de-lovecraft

Lovecraft  - 5.0€
https://es.wallapop.com/item/lovecraft

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

On macOS, install [`terminal-notifier`](https://github.com/julienXX/terminal-notifier) (`brew install terminal-notifier`) to make the notification clickable — it opens your Wallapop search results page (with your keywords, price range, and location filters applied) directly in the browser. Without it, macOS falls back to a plain `osascript` notification that isn't clickable.

### Notifying through Telegram

Add `--telegram` to the command line and it will send a notification to your Telegram.

You need to create a bot (@BotFather), get its token and your internal id (@RawDataBot), then copy `.env.example` to `.env` and fill it in:

```
TELEGRAM_BOT_TOKEN="1234567890:XXX"
TELEGRAM_CHAT_ID="1234567"
```

`.env` is gitignored, so your real token/chat ID never get committed. `.env.example` stays in the repo as the template.

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

### Running on Koyeb

> **Note:** Koyeb's free tier only supports web services (which sleep after inactivity). Worker services require a paid plan — the cheapest is `eco-nano` at ~$1.61/month, still cheaper than Heroku.

Koyeb ignores the `worker:` prefix in the Procfile, so the run command must be set explicitly in the service config.

**1. Create a Worker service in the Koyeb dashboard:**

- Source: GitHub → select your `wallasearch` repo, branch `master`
- Builder: Buildpack (auto-detects Python via `requirements.txt`)
- Run command: `python wallasearch.py --telegram`
- Service type: **Worker**
- Instance: `eco-nano`
- Region: Frankfurt or Washington D.C.

**2. Set environment variables** in the service settings:

```
WHAT_TO_SEARCH=Lovecraft
TELEGRAM_BOT_TOKEN=1234567890:XXX
TELEGRAM_CHAT_ID=1234567
POSTAL_CODE=28012
```

`POSTAL_CODE` is important — Koyeb servers are in Frankfurt or Washington D.C., so geo-IP won't give you local results.

**3. Deploy** — Koyeb will build and start the worker automatically on every push to `master`.

**Via CLI:**

```bash
koyeb apps create wallasearch
koyeb services create wallasearch \
  --app wallasearch \
  --git github.com/YOUR_USERNAME/wallasearch \
  --git-branch master \
  --git-buildpack-run-command "python wallasearch.py --telegram" \
  --type worker \
  --instance-type eco-nano \
  --region was \
  --env WHAT_TO_SEARCH=Lovecraft \
  --env TELEGRAM_BOT_TOKEN=your_token \
  --env TELEGRAM_CHAT_ID=your_chat_id \
  --env POSTAL_CODE=28012
```

### Running on GitHub Actions (free)

A ready-to-use workflow lives at `.github/workflows/wallasearch.yml`. It does **not**
run automatically — it only starts a "watch" when you manually trigger it, then
checks every 30 minutes until it expires or you stop it. State (the pickle file
and the active search config) is committed to `.github/wallasearch-state/` so
progress survives between runs.

**1. Add repo secrets** (Settings → Secrets and variables → Actions):

```
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

**2. Start a watch** (via GitHub UI: Actions → Wallasearch → Run workflow, or via `gh`):

```bash
gh workflow run wallasearch.yml \
  -f search="Lovecraft" \
  -f country="ES" \
  -f postal_code="28012"
```

This runs an immediate check and then re-checks every 30 minutes indefinitely.
Optionally pass `-f duration_hours="24"` to auto-stop after that many hours instead.

**3. Stop it early at any time:**

```bash
gh workflow run wallasearch.yml -f stop=true
```

**4. Check progress:**

```bash
gh run list --workflow=wallasearch.yml
```

Only one watch (search term) can be active at a time; starting a new one replaces
the previous config.

### Adding search term in .env

You can add the term to search in the `.env` file to avoid typing it every time:

```
WHAT_TO_SEARCH="Lovecraft"
```
