wallasearch
===========

Quick proyect for OSX in `Python3` to search for products in Wallapop, save them in pickle files and keep searching every X seconds (60 by default) to monitorize for new products. It will warn you when a new product is found with a notification in the system. If you find the text `a` it will create a file `a.pickle` with the results, so when you search for it again it will only show the new results.

### Usage

```python
~/wallasearch (master ✔) ᐅ ./wallasearch.py

################################################
# Author:   Sergio Ruiz                        #
# Github:   @serginator                        #
################################################
USAGE: ./wallasearch.py -s <terms_to_search>

OPTIONS:
  -h, --help
  -s, --search <terms> (if more than one word, use quotes)
  -t, --time <time> (default 60, in seconds)
      --city <city> (default Madrid)
      --country <country_code> (default ES)
~/wallasearch ᐅ ./wallasearch.py -s "Lovecraft"
Searching Lovecraft...
New items:

Cthulhu 6 figuras de resina - 15.0
Juego de LOVECRAFT - 25.0
Lovecraft  - 5.0
...

Searching Lovecraft...
Searching Lovecraft... (every X seconds)
```

### Config

In the script file there are three constants that you can modify

```python
# default
LOOP_TIME = 60; # seconds between executions by default
USER_CITY = "Madrid"; # city to search by default
COUNTRY_CODE = "ES"; # country code to search by default
```
