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
@bot.command(name="salary")
async def delete_messages(ctx: discord.ApplicationContext):
    await ctx.message.delete()
    await cron_send_statistics()
