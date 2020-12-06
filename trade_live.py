import sys
import time
import bitmex
import datetime
from src.Models import BTX
from src.Models import Position
from src.Connector import Database

# Trading initialize parameters
symbol = 'XBTUSD'
ordType = 'Market'
orderQty = 30
leverage = 10
diff_signal = 30
take_profit = 15
stop_loss = 5
# Opti setup 30 15 5
max_concurrent_positions = 1
open_positions = []

# Initialize API
bitmex_api_key = 'WaD4DpadS8c5oUiCFx5VwbNv'
bitmex_api_secret = 'LK_qSAqt3wpZ1BDmH9y00Pi62q3tTblCrlkRd2cq8MlUqjlQ'
api = bitmex.bitmex(test=False, api_key=bitmex_api_key, api_secret=bitmex_api_secret)

# Initialize Database
db = Database()
db.migrate_init()
session = db.create_session()

# Setup trading session.
api.Position.Position_updateLeverage(symbol=symbol, leverage=leverage)


def open_pos(direction, tick_id):
    # Open Pos: Order.Order_new(symbol=symbol, ordType=ordType, side=direction, orderQty=orderQty).result()
    if direction == 'Sell':
        orderQty = -orderQty
    else:
        orderQty = orderQty
    result = api.Order.Order_new(symbol=symbol, ordType=ordType, side=direction, orderQty=orderQty).result()
    if result['ordStatus'] == 'Filled':
        pos = Position(open_time=result['timestamp'], close_time='', symbol=result['symbol'], qty=result['orderQty'],
                       tick_id=tick_id, entry_price=result['price'], close_price='0', direction=result['side'],
                       order_id=result['orderID'])
        session.add(pos)
        session.commit()
        print("Opened Position:", pos.__dict__)
        return position
    else:
        return


def close_pos(position):
    # Close Pos: Order.Order_new(symbol='XBTUSD', ordType=ordType, execInst='Close').result()
    result = api.Order.Order_new(symbol='XBTUSD', ordType=ordType, execInst='Close').result()
    if result['ordStatus'] == 'Filled':
        session.query(Position).filter(Position.id == position.id).update({'close_price': result['price'],
                                                                           'close_time': result['timestamp']})
        session.commit()
        print("Closed position:", position.__dict__)
        open_positions.remove(position)
        return True
    else:
        time.sleep(0.2)
        return False


old_tick = ''
while True:
    tick = session.query(BTX).order_by(BTX.id.desc()).first()[0]
    diff = tick.ETF_PRICE - resultIDX_PRICE
    if tick != old_tick:
        if len(open_positions) < max_concurrent_positions:
            if diff > diff_signal:
                open_positions.append(open_pos('Sell', tick.id))
            elif DIFF < -diff_signal:
                open_positions.append(open_pos('Buy', tick.id))
    for position in open_positions:
        if position.direction == 'Sell' and \
           (tick.ETF_PRICE >= position.open_price + stop_loss or tick.ETF_PRICE <= position.open_price - take_profit):
            while not close_pos(position):
                pass
        if position.direction == 'Buy' and \
           (tick.ETF_PRICE <= position.open_price - stop_loss or tick.ETF_PRICE >= position.open_price + take_profit):
            while not close_pos(position):
                pass

    old_tick = tick
