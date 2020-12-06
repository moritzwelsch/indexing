from sqlalchemy import Table, Column, Date, Integer, String, ForeignKey, Text, TIMESTAMP, Sequence
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class BTX(Base):
    __tablename__ = 'PRICES'

    id = Column(Integer, Sequence('btx_id_seq'), primary_key=True)
    time = Column(Text)
    btx_etf_price = Column(Text)
    btx_idx_price = Column(Text)

    def __init__(self, time=None, btx_etf_price=None, btx_idx_price=None):
        self.time = time
        self.btx_etf_price = btx_etf_price
        self.btx_idx_price = btx_idx_price


class Position(Base):
    __tablename__ = 'POSITIONS'

    id = Column(Integer, Sequence('pos_id_seq'), primary_key=True)
    open_time = Column(Text)
    close_time = Column(Text)
    tick_id = Column(Text)
    qty = Column(Text)
    entry_price = Column(Text)
    close_price = Column(Text)
    direction = Column(Text)
    order_id = Column(Text)
    symbol = Column(Text)

    def __init__(self, open_time=None, close_time=None, tick_id=None, qty=None, entry_price=None, close_price=None,
                 direction=None, order_id=None, symbol=None):
        self.open_time = open_time
        self.close_time = close_time
        self.tick_id = tick_id
        self.qty = qty
        self.entry_price = entry_price
        self.close_price = close_price
        self.direction = direction
        self.order_id = order_id
        self.symbol = symbol
