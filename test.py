import sys
import ccxt
import json
import time
import datetime
import pandas as pd
from binance.client import Client
from src.Models import BTX_BINANCE
from src.Connector import Database
from src.Models import Position_Binance

# Get input parameter
if len(sys.argv) != 2:
    print("Please call <python-script> trading=True/False")
    sys.exit()
if sys.argv[1].split('=')[0] != 'trading':
    print("Only <trading> as parameter allowed. Following values: True/False")
    sys.exit()
else:
    if sys.argv[1].split('=')[1] == 'True':
        trading = True
    elif sys.argv[1].split('=')[1] == 'False':
        trading = False
    else:
        print("Only True/False allowed.")
        sys.exit()

# Trading parameters
symbol = 'BTCUSDT'
qty = 0.02
take_profit = 60
stop_loss = 20
max_spread = 0.5
max_position_count = 1
min_change = 0.01
minutes = [5, 10, 15]
max_minute = max(minutes)

# Exchange parameters
fees = (0.04 / 100) * 2

# Initialize Database
db = Database()
db.migrate_init()
session = db.create_session()

# API Settings
api_key = 'WdoRwblecwrql65DBuBAbPD05PKq0hYNQqREBJsI9j44FYzjTdBIjPrbCNEMP5bK'
api_secret = '6JmhkmSQVD2DJlb54KBjMjNtz9AwU9DJ7Rjav2IvHYyMzWMNce5L0fxYnwsZpe7G'
api = Client(api_key, api_secret)


def build_dataframe():
    rows = []
    for row in session.query(BTX_BINANCE).order_by(BTX_BINANCE.id.desc()).limit(max_minute * 300):
        # print(pd.Timestamp(row.time), pd.Timestamp(datetime.datetime.now()) - datetime.timedelta(minutes=max_minute))
        if pd.Timestamp(row.time) > pd.Timestamp(datetime.datetime.now()) - datetime.timedelta(minutes=max_minute):
            row_dict = {'TIME': row.time, 'BID': row.bid, 'ASK': row.ask, 'SPREAD': row.spread}
            rows.append(row_dict)
    if not rows:
        df = pd.DataFrame(columns=['TIME', 'BID', 'ASK', 'SPREAD'])
        df.set_index('TIME', inplace=True)
        return df
    df = pd.DataFrame(rows)
    df['TIME'] = pd.to_datetime(df['TIME'], format='%Y-%m-%d %H:%M:%S.%f')
    df = df.set_index('TIME')
    df['BID'] = pd.to_numeric(df['BID'])
    df['ASK'] = pd.to_numeric(df['ASK'])
    df['SPREAD'] = pd.to_numeric(df['SPREAD'])
    df.sort_index(inplace=True)
    return df


def get_signal(df):
    dataframes = []
    for minute in minutes:
        dataframe = pd.DataFrame()
        for index, row in df.iterrows():
            if pd.Timestamp(index) > pd.Timestamp(datetime.datetime.now()) - datetime.timedelta(minutes=minute):
                row = pd.DataFrame(data={'BID': row['BID'], 'ASK': row['ASK'],
                                         'SPREAD': row['SPREAD']}, index=[pd.Timestamp(index)])
                dataframe = dataframe.append(row)
        # print(dataframe)
        dataframes.append(dataframe)
    changes = []
    for rows in dataframes:
        change = (rows.tail(1)['BID'].item() - rows.head(1)['BID'].item())\
                 / rows.head(1)['BID'].item() * 100
        changes.append(change)

    if all(i > min_change for i in changes):
        return 'BUY'
    elif all(i < -min_change for i in changes):
        return 'SELL'
    else:
        return


def get_all_positions():
    result = api.futures_get_all_orders(
        symbol=symbol
    )
    return result


def get_position_status(order_id):
    result = api.futures_get_order(
        symbol=symbol,
        orderId=order_id
    )
    return result


def open_position(side, tick_id):
    if side == 'SELL':
        side = api.SIDE_SELL
    elif side == 'BUY':
        side = api.SIDE_BUY
    else:
        print("ERROR - Side not valid.", side)
        return

    result = api.futures_create_order(
        symbol=symbol,
        side=side,
        type=Client.ORDER_TYPE_MARKET,
        quantity=qty
    )
    counter = 0
    while result['status'] != 'FILLED':
        result = get_position_status(result['orderId'])
        if result['status'] != 'FILLED':
            time.sleep(0.1)
            counter += 1
            if counter >= 1000:
                print("ERROR - Position could not be opened.")
                return
            continue
    else:
        pos = Position_Binance(open_time=result['time'], close_time='', symbol=result['symbol'],
                               qty=float(result['executedQty']), tick_id=tick_id, entry_price=float(result['avgPrice']),
                               close_price='0', direction=result['side'], order_id=result['orderId'])
        session.add(pos)
        session.commit()
        print("Opened Position:", pos.open_time, pos.direction, pos.entry_price, pos.qty)
        return pos


def close_position(pos):
    if pos.direction == 'SELL':
        side = api.SIDE_BUY
    elif pos.direction == 'BUY':
        side = api.SIDE_SELL
    else:
        print("ERROR - Side not valid.", pos.side)
        return

    result = api.futures_create_order(
        symbol=symbol,
        side=side,
        type=api.ORDER_TYPE_MARKET,
        quantity=qty
    )
    counter = 0
    while result['status'] != 'FILLED':
        result = get_position_status(result['orderId'])
        if result['status'] != 'FILLED':
            time.sleep(0.1)
            counter += 1
            if counter >= 1000:
                print("ERROR - Position could not be opened.")
                return
            continue
    else:
        session.query(Position_Binance).filter(Position_Binance.id == pos.id).update({'close_price': float(result['avgPrice']),
                                                                           'close_time': result['time']})
        session.commit()
        print("Closed position:", pos.close_time, pos.close_price)
        return True


profit = 0
open_positions = []
df = build_dataframe()
old_data = {'price': 0}
while True:
    start = time.time()
    data = api.futures_symbol_ticker(symbol='BTCUSDT')
    if data and data['price'] != old_data['price']:
        now = str(datetime.datetime.now())
        spread = float(data['price']) - float(data['price'])
        # print(now, data['a'], data['b'], spread)
        old_data = data
        row = pd.DataFrame(data={'BID': float(data['price']), 'ASK': float(data['price']),
                                 'SPREAD': spread}, index=[pd.Timestamp(now)])
        df = df.append(row)

        # Update database
        row = BTX_BINANCE(time=now, bid=data['price'], ask=data['price'], spread=str(spread))
        session.add(row)
        session.commit()

        # Check if oldest element in df is removable
        if df.head(1).index.item() < pd.Timestamp(now) - datetime.timedelta(minutes=max_minute + 0.1):
            df.drop(df.head(1).index, inplace=True)
        elif df.head(1).index.item() < pd.Timestamp(now) - datetime.timedelta(minutes=max_minute):
            pass
        else:
            print("Waiting for cache to build...", len(df))
            continue
        # print('LENGTH', len(df))
        # Getting signal to execute
        if not trading:
            sleep_time = 0.05 - (time.time() - start)
            if sleep_time < 0:
                continue
            else:
                time.sleep(sleep_time)
            continue
        signal = get_signal(df)
        if signal and spread <= max_spread and len(open_positions) < max_position_count:
            print(signal + '_' + data['price'])
            pos = open_position(signal, now)
            if pos:
                open_positions.append(pos)

        if len(open_positions) >= max_position_count:
            for position in open_positions:
                bid_price = float(data['price'])
                ask_price = float(data['price'])
                if position.direction == 'SELL' and \
                        (ask_price >= float(position.entry_price) + stop_loss or ask_price
                         <= float(position.entry_price) - take_profit):
                    print(position.direction, price, position.entry_price)
                    while not close_position(position):
                        pass
                    open_positions.remove(position)
                    continue
                elif position.direction == 'BUY' and \
                        (bid_price <= float(position.entry_price) - stop_loss or bid_price
                         >= float(position.entry_price) + take_profit):
                    print(position.direction, price, position.entry_price)
                    while not close_position(position):
                        pass
                    open_positions.remove(position)
                    continue

    sleep_time = 0.05 - (time.time() - start)
    if sleep_time < 0:
        continue
    else:
        time.sleep(sleep_time)
