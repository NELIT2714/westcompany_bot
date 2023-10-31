import datetime
import asyncio
import discord
import re

from discord.ext import commands
from discord.commands import Option

from project import bot, contracts, Base, Session, tasks, config, admin_roles
from project.models import Contracts, Coffers, DailyTasks, Users, Warehouse
from project.functions import is_owner, cron_send_statistics

from sqlalchemy import cast, Date, or_, and_


@bot.slash_command(name="пинг", description="Показывает информацию о боте")
async def ping(ctx: discord.ApplicationContext):
    current_time = datetime.datetime.now()
    uptime = current_time - bot.start_time
    hours = uptime.total_seconds() // 3600

    db_start_time = datetime.datetime.now()

    with Session() as session:
        session.query(Users).first()

    db_stop_time = datetime.datetime.now()

    query_time = (db_stop_time - db_start_time).total_seconds() * 1000

    embed = discord.Embed(color=discord.Color(0x18B542))
    embed.add_field(name="Время отклика бота", value=f"{round(bot.latency * 1000)} мс.", inline=False)
    embed.add_field(name="Время отклика БД", value=f"{query_time:.0f} мс.", inline=False)
    embed.add_field(name="Аптайм (время работы)", value=f"{int(hours)} часов {int(uptime.seconds/60)%60} минут", inline=False)
    embed.add_field(name="Версия бота", value=bot.version, inline=False)
    embed.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

    await ctx.defer(ephemeral=True)
    await ctx.respond(embed=embed, ephemeral=True)
