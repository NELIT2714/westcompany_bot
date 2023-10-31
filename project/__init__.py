import json
import discord
import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

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

engine = create_engine(f"mysql+pymysql://{user}:{password}@{host}/{database}")
Session = sessionmaker(bind=engine)

Base = declarative_base()

bot.version = config["bot"]["version"]

from project.functions import cron_send_statistics

scheduler = AsyncIOScheduler()
scheduler.add_job(
    cron_send_statistics,
    CronTrigger(day_of_week="sun", hour=23, minute=59),
    id="send_statistics"
)

admin_roles = [
    config["guild"]["ids-list"]["roles"]["leader"],
    config["guild"]["ids-list"]["roles"]["dep-leader"],
    config["guild"]["ids-list"]["roles"]["admin"],
    config["guild"]["ids-list"]["roles"]["manager"],
    config["guild"]["ids-list"]["roles"]["dep-manager"]
]
dev_channels = [
    config["guild"]["logs"]["server"],
    config["guild"]["logs"]["messages"],
    config["guild"]["logs"]["users"]
]

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

from project.events import on_ready, on_member_update, on_member_join, on_member_remove, on_message, on_message_edit, on_message_delete
from project.commands import cmd_ad, cmd_clear, cmd_coffers, cmd_contract, cmd_embed, cmd_info, cmd_member, cmd_ping, cmd_rept, cmd_salary, cmd_statistics, cmd_warehouse, cmd_profile, cmd_member_info
from project.models import Contracts, Coffers, DailyTasks, Users, Warehouse
