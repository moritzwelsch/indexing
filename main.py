import json
import time
import ccxt
import requests
import datetime
from bitmex_websocket import BitMEXWebsocket
from src.Connector import Database
from src.Models import BTX
from src.index_calculator import Index

# Initialize Index
index = Index()
index.get_weighting()
index_weighting_interval = 7200

# Initialize Database
db = Database()
db.migrate_init()
session = db.create_session()

# Initialize Websocket
bitmex_api_key = '7hpAgbRkeTMYp0tN6CyrSSiJ'
bitmex_api_secret = '6kqQuRrY9UHUtl-_BxTRmxMkTM6DKqRQ5H41PURRPafI8ASO'

api = ccxt.bitmex()
api.apiKey = bitmex_api_key
api.secret = bitmex_api_secret

# Run forever
counter = 0
old_tick = ''
while True:
    start = time.time()
    tick = api.fetch_ticker(symbol='BTC/USD')
    if counter == index_weighting_interval:
        counter = 0
        index.get_weighting()

    if old_tick != tick['bid']:
        now = datetime.datetime.now()
        index.get_index_value()
        row = BTX(time=str(now), btx_etf_price=str(tick['bid']), btx_idx_price=str(index.index_value))
        session.add(row)
        session.commit()
        print(str(now) + ' - Buy-Kurs: ' + str(tick['ask']) + ' Sell-Kurs: ' + str(tick['bid']), ' - Index: ' + str(index.index_value), ' - Diff: ', str(tick['last'] - index.index_value))
        old_tick = tick['bid']
        counter += 1
    sleep_time = 1.1 - (time.time() - start)
    if sleep_time < 0:
        continue
    else:
        time.sleep(sleep_time)
