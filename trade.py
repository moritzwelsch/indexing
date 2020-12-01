import sys
import numpy
import pandas as pd
from src.Models import BTX
import matplotlib.pyplot as plt
from src.Connector import Database

# Trading initialize parameters
money = 1000
leverage = 1           # Float Value. So 1.2 means 20% Leverage
position_size = money * leverage
fees = (0.075 / 100) * 2
diff_signal = 30
take_profit = 20
stop_loss = 10
spread = 0.5
max_concurrent_positions = 1
open_positions = []


# Initialize Database
db = Database()
db.migrate_init()
session = db.create_session()

rows = []
for row in session.query(BTX).all():
    # print(row.__dict__)
    row_dict = {'TIME': row.time, 'ETF_PRICE': row.btx_etf_price, 'IDX_PRICE': row.btx_idx_price}
    rows.append(row_dict)

df = pd.DataFrame(rows)
df['TIME'] = pd.to_datetime(df['TIME'], format='%Y-%m-%d %H:%M:%S.%f')
df = df.set_index('TIME')
df['ETF_PRICE'] = pd.to_numeric(df['ETF_PRICE'])
df['IDX_PRICE'] = pd.to_numeric(df['IDX_PRICE'])
df['DIFF'] = df.apply(lambda row: row.ETF_PRICE - row.IDX_PRICE, axis=1)

for index, row in df.iterrows():
    if len(open_positions) < max_concurrent_positions:
        if row.DIFF > diff_signal:
            # print("SELL", index, row.DIFF, row.ETF_PRICE, row.IDX_PRICE)
            open_positions.append('SELL_' + str(row.ETF_PRICE - 0.5))
        elif row.DIFF < -diff_signal:
            # print("BUY", index, row.DIFF, row.ETF_PRICE, row.IDX_PRICE)
            open_positions.append('BUY_' + str(row.ETF_PRICE + 0.5))
    else:
        for position in open_positions:
            direction = position.split('_')[0]
            entry_price = float(position.split('_')[1])
            profit = 0
            if direction == 'BUY' and row.ETF_PRICE >= entry_price + take_profit:
                fee = (position_size / entry_price) * fees
                profit = (((1/entry_price - 1/row.ETF_PRICE) * position_size) * row.ETF_PRICE) - fee
                money += profit
                print(direction, '-', money, '- TP HIT -', entry_price, row.ETF_PRICE, profit, fee)
                open_positions.remove(position)
                continue

            elif direction == 'SELL' and row.ETF_PRICE <= entry_price - take_profit:
                fee = (position_size / entry_price) * fees
                profit = abs((((1/row.ETF_PRICE - 1/entry_price) * position_size) * row.ETF_PRICE)) - fee
                money += profit
                print(direction, '-', money, '- TP HIT -', entry_price, row.ETF_PRICE, profit, fee)
                open_positions.remove(position)
                continue

            elif direction == 'BUY' and row.ETF_PRICE <= entry_price - stop_loss:
                fee = (position_size / entry_price) * fees
                profit = (((1 / entry_price - 1 / row.ETF_PRICE) * position_size) * row.ETF_PRICE) - fee
                money += profit
                print(direction, '-', money, '- SL HIT -', entry_price, row.ETF_PRICE, profit, fee)
                open_positions.remove(position)
                continue

            elif direction == 'SELL' and row.ETF_PRICE >= entry_price + stop_loss:
                fee = (position_size / entry_price) * fees
                profit = (((1 / row.ETF_PRICE - 1 / entry_price) * position_size) * row.ETF_PRICE) - fee
                money += profit
                print(direction, '-', money, '- SL HIT -', entry_price, row.ETF_PRICE, profit, fee)
                open_positions.remove(position)
                continue
