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
@bot.command(name="embed")
async def embed_message(ctx: discord.ApplicationContext, content, *, message: str):
    if content == "-":
        content = ""

    lines = message.split('\n')
    title = lines[0]
    description = '\n'.join(lines[1:])

    embed = discord.Embed(
        title=title,
        color=discord.Color(0xFFFFFF),
        description=description
    )

    embed.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

    await ctx.message.delete()
    await ctx.send(content, embed=embed)
