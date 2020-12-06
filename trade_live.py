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
take_profit = 15
stop_loss = 5
# Opti setup 30 15 5
spread = 0.5
max_concurrent_positions = 1
open_positions = []


# Initialize Database
db = Database()
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
