import json
import time
import ccxt
import requests
import datetime
import bitmex
import bravado
from src.Connector import Database
from src.Models import BTX
from src.index_calculator import Index

# Initialize Index
index = Index()
index.get_weighting()
index_weighting_interval = 14400

# Initialize Database
db = Database()
db.migrate_init()
session = db.create_session()

# Initialize Websocket
bitmex_api_key = 'WaD4DpadS8c5oUiCFx5VwbNv'
bitmex_api_secret = 'LK_qSAqt3wpZ1BDmH9y00Pi62q3tTblCrlkRd2cq8MlUqjlQ'

api = bitmex.bitmex(test=False, api_key=bitmex_api_key, api_secret=bitmex_api_secret)

# Run forever
counter = 0
old_tick = ''
while True:
    start = time.time()
    try:
        tick = api.Quote.Quote_get(symbol="XBTUSD", reverse=True, count=1).result()
        print(datetime.datetime.now(), tick[1].headers['x-ratelimit-limit'], tick[1].headers['x-ratelimit-remaining'], datetime.datetime.fromtimestamp(int(tick[1].headers['x-ratelimit-reset'])).strftime('%Y-%m-%d %H:%M:%S'))
    except bravado.exception.HTTPTooManyRequests:
        print("TooManyRequests")
        time.sleep(5)
        continue
    if counter == index_weighting_interval:
        counter = 0
        index.get_weighting()
    if old_tick != tick[0][0]['bidPrice']:
        now = datetime.datetime.now()
        index.get_index_value()
        row = BTX(time=str(now), btx_etf_price=str(tick[0][0]['bidPrice']), btx_idx_price=str(index.index_value))
        session.add(row)
        session.commit()
        print(str(now) + ' - Buy-Kurs: ' + str(tick[0][0]['askPrice']) + ' Sell-Kurs: ' + str(tick[0][0]['bidPrice']), ' - Index: ' + str(index.index_value), ' - Diff: ', str(tick[0][0]['bidPrice'] - index.index_value))
        old_tick = tick[0][0]['bidPrice']
        counter += 1
    sleep_time = 2.0 - (time.time() - start)
    if sleep_time < 0:
        continue
    else:
        time.sleep(sleep_time)
