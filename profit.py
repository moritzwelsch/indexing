from src.Connector import Database
from src.Models import Position_Binance
import datetime
import pandas as pd

db = Database()
session = db.create_session()

money = 30
leverage = 10
position_size = float(money * leverage)
fees = float((0.04 / 100) * 2)

for pos in session.query(Position_Binance).all():
	# if pd.Timestamp(pos.open_time) >= datetime.datetime.today() - datetime.timedelta(days=1):
	pos.close_price = float(pos.close_price)
	pos.entry_price = float(pos.entry_price)
	if pos.close_price and pos.close_price > 0:
		if pos.direction == 'Buy' or pos.direction == 'BUY':
			fee = (position_size / pos.entry_price) * fees
			# print(pos.direction, pos.entry_price, pos.close_price, fee)
			porift = profit = (((1/pos.entry_price - 1/pos.close_price) * position_size) * pos.close_price) - fee
			print(pos.open_time, pos.direction, pos.entry_price, pos.close_price, fee, profit)
		elif pos.direction == 'Sell' or pos.direction == 'SELL':
			fee = (position_size / pos.entry_price) * fees
			# print(pos.direction, pos.entry_price, pos.close_price, fee)
			porift = profit = (((1/pos.close_price - 1/pos.entry_price) * position_size) * pos.close_price) - fee
			print(pos.open_time, pos.direction, pos.entry_price, pos.close_price, fee, profit)
		else:
			profit = 0
		money += profit

print(money)
