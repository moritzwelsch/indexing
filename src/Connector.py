import os
from src.Models import Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base


class Database:
    def __init__(self):
        self.engine = create_engine('mysql+pymsql://prices:15082020Kk-123.@localhost/prices')
        self.base = Base

    def migrate_init(self):
        self.base.metadata.create_all(self.engine)
        return

    def create_session(self):
        Session = sessionmaker(bind=self.engine)
        return Session()
