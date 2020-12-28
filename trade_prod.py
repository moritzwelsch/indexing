import json
import time
import ccxt
import requests
import datetime
import bitmex
import bravado
from src.Models import BTX
from src.Models import Position
from src import index_calculator
from src.Connector import Database
import pandas as pd
import numpy

# Init Index
index = index_calculator.Index()
index.get_weighting()
index_renew = 86400

# Trading initialize parameters
symbol = 'XBTUSD'
ordType = 'Market'
leverage = 10
orderQty = 30
diff_signal = 30
take_profit = 15
stop_loss = 5

# Optimal setup 30 15 5
max_concurrent_positions = 1
open_positions = []

# Initialize Database
db = Database()
db.migrate_init()
session = db.create_session()

# Minutes set
min_change = 0.01
minutes = [5, 10, 15]
max_minute = max(minutes)
print(minutes, max_minute)

# Initialize Websocket
bitmex_api_key = 'WaD4DpadS8c5oUiCFx5VwbNv'
bitmex_api_secret = 'LK_qSAqt3wpZ1BDmH9y00Pi62q3tTblCrlkRd2cq8MlUqjlQ'
api = bitmex.bitmex(test=False, api_key=bitmex_api_key, api_secret=bitmex_api_secret)


result = api.Position.Position_updateLeverage(symbol=symbol, leverage=leverage).result()
print(result)


def open_pos(direction, tick_id, order_qty):
    # Open Pos: Order.Order_new(symbol=symbol, ordType=ordType, side=direction, orderQty=orderQty).result()
    if direction == 'Sell':
        orderQty = -order_qty
    else:
        orderQty = order_qty
    result = api.Order.Order_new(symbol=symbol, ordType=ordType, side=direction, orderQty=orderQty).result()[0]
    if result['ordStatus'] == 'Filled':
        pos = Position(open_time=result['timestamp'], close_time='', symbol=result['symbol'], qty=int(result['orderQty']),
                       tick_id=tick_id, entry_price=float(result['price']), close_price='0', direction=result['side'],
                       order_id=result['orderID'])
        session.add(pos)
        session.commit()
        print("Opened Position:", pos.open_time, pos.direction, pos.entry_price, pos.qty)
        return pos
    else:
        return


def close_pos(position):
    # Close Pos: Order.Order_new(symbol='XBTUSD', ordType=ordType, execInst='Close').result()
    result = api.Order.Order_new(symbol='XBTUSD', ordType=ordType, execInst='Close').result()[0]
    if result['ordStatus'] == 'Filled':
        session.query(Position).filter(Position.id == position.id).update({'close_price': float(result['price']),
                                                                           'close_time': result['timestamp']})
        session.commit()
        print("Closed position:", position.close_time, position.close_price)
        open_positions.remove(position)
        return True
    else:
        time.sleep(0.2)
        return False


def get_data():
    rows = []
    for row in session.query(BTX).order_by(BTX.id.desc()).limit(max_minute * 60):
        if pd.Timestamp(row.time) > pd.Timestamp(datetime.datetime.now()) - datetime.timedelta(minutes=max_minute):
            row_dict = {'TIME': row.time, 'ETF_PRICE': row.btx_etf_price}
            rows.append(row_dict)

    df = pd.DataFrame(rows)
    df['TIME'] = pd.to_datetime(df['TIME'], format='%Y-%m-%d %H:%M:%S.%f')
    df = df.set_index('TIME')
    df['ETF_PRICE'] = pd.to_numeric(df['ETF_PRICE'])
    df.sort_index(inplace=True)
    return df


def get_change(rows):
    # print(rows.head(1).index.item(), rows.head(1)['ETF_PRICE'].item(), rows.tail(1).index.item(),
    # rows.tail(1)['ETF_PRICE'].item(), rows.tail(1)['ETF_PRICE'].item())
    change = (rows.tail(1)['ETF_PRICE'].item() - rows.head(1)['ETF_PRICE'].item()) / rows.head(1)['ETF_PRICE'].item() * 100
    return change


# Run forever
counter = 0
old_tick = ''
df = get_data()
while True:
    start = time.time()
    try:
        tick = api.Quote.Quote_get(symbol="XBTUSD", reverse=True, count=1).result()
        # print(datetime.datetime.now(), tick[1].headers['x-ratelimit-limit'], tick[1].headers['x-ratelimit-remaining'],
        # datetime.datetime.fromtimestamp(int(tick[1].headers['x-ratelimit-reset'])).strftime('%Y-%m-%d %H:%M:%S'))
    except (bravado.exception.HTTPTooManyRequests, bravado.exception.HTTPBadRequest):
        print("TooManyRequests")
        time.sleep(5)
        continue
    if old_tick != tick[0][0]['bidPrice']:

        now = datetime.datetime.now()
        row = pd.DataFrame(data={'ETF_PRICE': float(tick[0][0]['bidPrice'])}, index=[now])
        df = df.append(row)
        old_tick = tick[0][0]['bidPrice']

        # Filtering out if oldest element is older than now minus max minutes specified on top.
        if df.head(1).index.item() < now - datetime.timedelta(minutes=max_minute):
            df.drop(df.head(1).index, inplace=True)
        # Opening positions on condition
        if len(open_positions) < max_concurrent_positions:
            change = get_change(df)
            if change > min_change:
                open_positions.append(open_pos('Sell', str(now), orderQty))
            elif change < -min_change:
                open_positions.append(open_pos('Buy', str(now), orderQty))

        # Inserting database row
        row = BTX(time=str(now), btx_etf_price=str(tick[0][0]['bidPrice']))
        session.add(row)
        session.commit()
        # print(str(now) + ' - Buy-Kurs: ' + str(tick[0][0]['askPrice']) + ' Sell-Kurs: ' + str(tick[0][0]['bidPrice']))

        # Closing positions on condition
        for position in open_positions:
            if position.direction == 'Sell' and \
                    (float(tick[0][0]['askPrice']) >= float(position.entry_price) + stop_loss or float(
                        tick[0][0]['askPrice']) <= float(position.entry_price) - take_profit):
                while not close_pos(position):
                    pass
            if position.direction == 'Buy' and \
                    (float(tick[0][0]['askPrice']) <= float(position.entry_price) - stop_loss or float(
                        tick[0][0]['askPrice']) >= float(position.entry_price) + take_profit):
                while not close_pos(position):
                    pass

        # Counter setting
        old_tick = tick[0][0]['bidPrice']
        counter += 1
    sleep_time = 1.3 - (time.time() - start)
    if sleep_time < 0:
        continue
    else:
        time.sleep(sleep_time)
