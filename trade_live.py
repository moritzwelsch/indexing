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


# Setup trading session.
api.Position.Position_updateLeverage(symbol=symbol, leverage=leverage)


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
        print("Opened Position:", pos.__dict__)
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
        print("Closed position:", position.__dict__)
        open_positions.remove(position)
        return True
    else:
        time.sleep(0.2)
        return False


old_tick = '1'
while True:
    session = db.create_session()
    tick = session.query(BTX).order_by(BTX.id.desc()).first()
    tick.btx_etf_price = float(tick.btx_etf_price)
    tick.btx_idx_price = float(tick.btx_idx_price)
    diff = tick.btx_etf_price - tick.btx_idx_price
    if tick.btx_etf_price != old_tick:
        print(datetime.datetime.now(), tick.__dict__, diff)
        if len(open_positions) < max_concurrent_positions:
            if diff > diff_signal:
                open_positions.append(open_pos('Sell', tick.id, orderQty))
            elif diff < -diff_signal:
                open_positions.append(open_pos('Buy', tick.id, orderQty))
    for position in open_positions:
        if position.direction == 'Sell' and \
                (float(tick.btx_etf_price) >= float(position.entry_price) + stop_loss or float(tick.btx_etf_price) <= float(position.entry_price) - take_profit):
            while not close_pos(position):
                pass
        if position.direction == 'Buy' and \
           (float(tick.btx_etf_price) <= float(position.entry_price) - stop_loss or float(tick.btx_etf_price) >= float(position.entry_price) + take_profit):
            while not close_pos(position):
                pass
    old_tick = tick.btx_etf_price + 0
    session.close()
    time.sleep(0.01)

