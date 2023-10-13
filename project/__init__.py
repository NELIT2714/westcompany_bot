import json

import discord
from discord.ext import commands

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Intents
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
intents.members = True
intents.presences = True
intents.bans = True

with open("config.json") as config:
    config = json.load(config)

token = config["bot"]["token"]
prefix = config["bot"]["prefix"]

host = config["db"]["host"]
database = config["db"]["database"]
user = config["db"]["user"]
password = config["db"]["password"]
port = config["db"]["port"]

bot = commands.Bot(command_prefix=prefix, intents=intents)
bot.remove_command("help")

# Database
engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}/{database}")
Session = sessionmaker(bind=engine)

Base = declarative_base()

bot.version = config["bot"]["version"]

contracts = [
    {"name": "Монетный двор", "cooldown": 24, "price": 100000, "reward": 500000,
     "description": "Скупщик договорился на крупную партию золотых монет, нужно помочь ему их найти, он щедро заплатит."},
    {"name": "Крупный банкет", "cooldown": 24, "price": 200000, "reward": 500000,
     "description": "Один из влиятельных людей Лос-Сантоса проводит крупный банкет, ресторану срочно нужны продукты "
                    "чтобы успеть подготовить блюда на всех."},
    {"name": "Налётчики", "cooldown": 24, "price": 300000, "reward": 2000000,
     "description": "Ваша группировка быстро растет, необходимо заявить о себе всему криминальному миру Лос-Сантоса."},
    {"name": "Рыбный промысел", "cooldown": 48, "price": 500000, "reward": 3000000,
     "description": "Крупному поставищку срочно нужна крупная партия рыбы, он на награду не скупится."}
]
tasks = []

from project.commands import collection, warehouse, contract, coffers, ping, statistic, rept
from project.events import on_ready
from project.models import Contracts, Coffers, DailyTasks, Users, Warehouse
