import datetime

from sqlalchemy import Column, Integer, String, Boolean, Date, BigInteger, Text
from project import Base


class Contracts(Base):
    __tablename__ = "wc_contracts"

    id = Column(Integer, primary_key=True)
    discord_user = Column(BigInteger, nullable=False)
    contract_name = Column(String(30), nullable=True)
    price = Column(Integer, nullable=True)
    reward = Column(Integer, nullable=True)
    status = Column(Boolean, unique=False, nullable=True)
    date = Column(Date, default=datetime.datetime.now())

    def __init__(self, discord_user, contract_name, price, reward, status):
        self.discord_user = discord_user
        self.contract_name = contract_name
        self.price = price
        self.reward = reward
        self.status = status


class Coffers(Base):
    __tablename__ = "wc_coffers"

    id = Column(Integer, primary_key=True)
    discord_user = Column(BigInteger, nullable=False)
    action = Column(String(30), nullable=True)
    amount = Column(BigInteger, nullable=False)
    date = Column(Date, default=datetime.datetime.now())

    def __init__(self, discord_user, action, amount):
        self.discord_user = discord_user
        self.action = action
        self.amount = amount


class DailyTasks(Base):
    __tablename__ = "wc_daily-tasks"

    id = Column(Integer, primary_key=True)
    discord_user = Column(BigInteger, nullable=False)
    type_rept = Column(String(50), nullable=False)
    url = Column(Text, nullable=False)
    date = Column(Date, default=datetime.datetime.now())

    def __init__(self, discord_user, type_rept, url):
        self.discord_user = discord_user
        self.type_rept = type_rept
        self.url = url


class Users(Base):
    __tablename__ = "wc_users"

    id = Column(Integer, primary_key=True)
    discord_user = Column(BigInteger, nullable=False, unique=True)
    nickname = Column(String(50), nullable=False)
    date = Column(Date, default=datetime.datetime.now())

    def __init__(self, discord_user, nickname):
        self.discord_user = discord_user
        self.nickname = nickname


class Warehouse(Base):
    __tablename__ = "wc_warehouse"

    id = Column(Integer, primary_key=True)
    discord_user = Column(BigInteger, nullable=False)
    action = Column(String(30), nullable=True)
    item = Column(Text, nullable=False)
    date = Column(Date, default=datetime.datetime.now())

    def __init__(self, discord_user, action, item):
        self.discord_user = discord_user
        self.action = action
        self.item = item
