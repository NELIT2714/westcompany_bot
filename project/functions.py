import discord
import datetime
import asyncio

from discord.ext import commands
from discord.commands import Option
from project import bot, engine, Base, Session, salary
from project.models import Contracts, Coffers, DailyTasks, Users, Warehouse
from sqlalchemy import cast, Date, or_, and_


def is_owner(ctx):
    return ctx.author.id == 463277343150964738


async def send_statistics():
    guild = bot.get_guild(1107054342223167623)
    role_member = guild.get_role(1107286502825795624)
    channel = guild.get_channel(1150832578018943118)

    start_of_week = datetime.datetime.now() - datetime.timedelta(days=datetime.datetime.now().weekday())

    user_stats = ""

    for member in guild.members:
        if role_member in member.roles:
            with Session() as session:
                user = session.query(Users).filter_by(discord_user=member.id).first()

                if user is None:
                    continue

                daily_tasks = session.query(DailyTasks).filter(
                    DailyTasks.date >= start_of_week.date()).filter(
                    DailyTasks.date <= datetime.datetime.now().date()
                ).filter_by(discord_user=member.id).count()

            user_salary = daily_tasks * salary
            user_stats += f"- {user.nickname} // {daily_tasks} ежедневных заданий // {'{0:,}'.format(user_salary).replace(',', '.')}$\n"

    statistics_embed = discord.Embed(
        title=f"Зарплаты участников за период {start_of_week.strftime('%d-%m-%Y')} - {datetime.datetime.now().strftime('%d-%m-%Y')}",
        description=f"Ежедневные задания:\n{user_stats}",
        color=0xFFFFFF
    )
    statistics_embed.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

    await channel.send(embed=statistics_embed)


async def cron_send_statistics():
    await send_statistics()
