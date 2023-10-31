import discord
import datetime
import asyncio

from discord.ext import commands
from discord.commands import Option
from project import bot, engine, Base, Session, config
from project.models import Contracts, Coffers, DailyTasks, Users, Warehouse
from sqlalchemy import cast, Date, or_, and_


def is_owner(ctx):
    return ctx.author.id == 463277343150964738


async def send_statistics():
    guild = bot.get_guild(config["guild"]["id"])
    role_member = guild.get_role(config["guild"]["ids-list"]["roles"]["member"])
    channel = guild.get_channel(config["guild"]["ids-list"]["channels"]["statistics"])

    start_of_week = datetime.datetime.now() - datetime.timedelta(days=datetime.datetime.now().weekday())

    users_stats = []

    for member in guild.members:
        if role_member in member.roles:
            with Session() as session:
                user = session.query(Users).filter_by(discord_user=member.id).first()

                if user is None:
                    continue

            with Session() as session:
                daily_tasks = session.query(DailyTasks).filter(
                    DailyTasks.date >= start_of_week.date()).filter(
                    DailyTasks.date <= datetime.datetime.now().date()
                ).filter_by(discord_user=member.id).count()

            user_salary = daily_tasks * int(config["other"]["salary"]["daily-task"])

            user_stats = {
                "nickname": user.nickname,
                "member": member.mention,
                "daily_tasks": daily_tasks,
                "salary": user_salary
            }

            users_stats.append(user_stats)

    users_stats_text = ""
    users_salary = 0
    users_tasks = 0

    statistics_embed = discord.Embed(
        title=f"Зарплаты участников за период {start_of_week.strftime('%d-%m-%Y')} - {datetime.datetime.now().strftime('%d-%m-%Y')}",
        color=0xFFFFFF
    )

    for user in users_stats:
        if user["salary"] >= 1:
            users_stats_text += f"- {user['nickname']} | {user['member']} | {user['daily_tasks']} ежедневных заданий | {'{0:,}'.format(user['salary']).replace(',', '.')}$\n"
            users_salary += user["salary"]
            users_tasks += user["daily_tasks"]
        else:
            continue

    if not users_tasks == 0:
        users_stats.sort(key=lambda x: x["salary"], reverse=True)

        statistics_embed.description = f"Ежедневные задания:\n{users_stats_text}\nУчастники, которые имеют менее чем 1 выполненное задание скрыты из списка."
        statistics_embed.add_field(name="Сумма выплат", value=f"{'{0:,}'.format(users_salary).replace(',', '.')}$", inline=True)
        statistics_embed.add_field(name="Выполненно заданий", value=str(users_tasks), inline=True)
    else:
        statistics_embed.description = "Упс... За указанный период в базе не найдено ни одного отчёта о выполнении ежедневных заданий."

    statistics_embed.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

    await channel.send(embed=statistics_embed)

async def cron_send_statistics():
    await send_statistics()
