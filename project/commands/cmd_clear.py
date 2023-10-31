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


@commands.check(is_owner)
@bot.command(name="clear")
async def delete_messages(ctx: discord.ApplicationContext, amount: int):
    await ctx.channel.purge(limit=amount + 1)
