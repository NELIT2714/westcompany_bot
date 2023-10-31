import discord
import datetime

from project import bot, contracts, Base, Session, config, admin_roles, engine
from project.models import Contracts, Coffers, DailyTasks, Users

from sqlalchemy import cast, Date, or_, and_


@bot.event
async def on_ready():
    bot.start_time = datetime.datetime.now()
    Base.metadata.create_all(engine)
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(name=config["bot"]["activity"])
    )
    print(f"Logged in as {bot.user.name} | ID: {bot.user.id}")