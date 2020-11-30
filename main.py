import json
import bitmex
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
bitmex_api_key = 'dmhw7WzhowGv-azLLUilvrj2'
bitmex_api_secret = 'GHxloPld3Al36gFbjDvPuOVd_1NoKrZU-UA8Y_vI-GgUuaUh'

ws = BitMEXWebsocket(
    endpoint="https://www.bitmex.com/api/v1",
    symbol="XBTUSD",
    api_key=bitmex_api_key,
    api_secret=bitmex_api_secret
)

ws.get_instrument()

# Run forever
counter = 0
old_tick = ''
while ws.ws.sock.connected:
    tick = ws.get_ticker()
    if counter == index_weighting_interval:
        counter = 0
        index.get_weighting()

    if old_tick != tick:
        now = datetime.datetime.now()
        index.get_index_value()
        row = BTX(time=str(now), btx_etf_price=str(tick['last']), btx_idx_price=str(index.index_value))
        session.add(row)
        session.commit()
        print(str(now) + ' - Kurs: ' + str(tick['last']), ' - Index: ' + str(index.index_value), ' - Diff: ', str(tick['last'] - index.index_value))
        old_tick = tick
        counter += 1
