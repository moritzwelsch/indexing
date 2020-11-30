import sys
import numpy
import pandas as pd
from src.Models import BTX
import matplotlib.pyplot as plt
from src.Connector import Database

# Initialize Database
db = Database()
db.migrate_init()
session = db.create_session()

all = session.query(BTX).all()

rows = []
for row in all:
    print(row.__dict__)
    row_dict = {'TIME': row.time, 'ETF_PRICE': row.btx_etf_price, 'IDX_PRICE': row.btx_idx_price}
    rows.append(row_dict)


# Create the x-axis data
df = pd.DataFrame(rows)
df['TIME'] = pd.to_datetime(df['TIME'], format='%Y-%m-%d %H:%M:%S.%f')
df = df.set_index('TIME')
dates = df.index.to_series()
dates = [pd.to_datetime(d) for d in dates]

# Create the y-axis data

etf_price = pd.to_numeric(df['ETF_PRICE'])
idx_price = pd.to_numeric(df['IDX_PRICE'])
print(etf_price, idx_price)

# Add titles to the chart and axes
plt.figure(figsize=(18, 9))
plt.style.use('seaborn-whitegrid')
plot_etf, = plt.plot(dates, etf_price)
plot_idx, = plt.plot(dates, idx_price)
plt.legend(['ETF', 'Index'])
plt.title('ETF vs Index Pice correlation')
plt.show()
