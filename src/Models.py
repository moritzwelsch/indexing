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

