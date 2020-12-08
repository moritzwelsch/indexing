from src.Connector import Database
from src.Models import Position

db = Database()
session = db.create_session()

money = 30
leverage = 10
position_size = money * leverage
fees = (0.075 / 100) * 2

for pos in session.query(Position).all():
	if pos.close_price:
		if pos.direction == 'Buy':
			fee = (position_size / pos.entry_price) * fees
			porift = profit = (((1/pos.entry_price - 1/pos.close_price) * position_size) * pos.close_price) - fee
			print(pos.direction, pos.entry_price, pos.close_price, fee)
		elif pos.direction == 'Sell':
			fee = (position_size / pos.entry_price) * fees
			porift = profit = (((1/pos.close_price - 1/pos.entry_price) * position_size) * pos.close_price) - fee
			print(pos.direction, pos.entry_price, pos.close_price, fee)




