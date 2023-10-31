import datetime
import asyncio
import discord
import re
import matplotlib.pyplot as plt

from io import BytesIO

from discord.ext import commands
from discord.commands import Option

from project import bot, contracts, Base, Session, tasks, config, admin_roles
from project.models import Contracts, Coffers, DailyTasks, Users, Warehouse
from project.functions import is_owner, cron_send_statistics

from sqlalchemy import cast, Date, or_, and_


@bot.slash_command(name="статистика", description="Выводит статистику бота")
async def statistics(ctx: discord.ApplicationContext,
                     start_date: Option(str, description="Начальная дата (дд-мм-гггг)"),
                     end_date: Option(str, description="Конечная дата (дд-мм-гггг)")):

    with Session() as session:
        user = session.query(Users).filter_by(discord_user=ctx.author.id).first()

    channel_statistics = ctx.guild.get_channel(config["guild"]["ids-list"]["channels"]["statistics"])

    if ctx.channel.type == discord.ChannelType.private:
        embed_error = discord.Embed(
            title="Ошибка",
            description="Вы не можете отправлять команды боту в личные сообщения.",
            color=discord.Color(0xFF0000)
        )
        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    if not any(admin_role.id in admin_roles for admin_role in ctx.author.roles):
        embed_error = discord.Embed(
            title="Ошибка",
            description="У вас нет прав",
            color=discord.Color(0xFF0000)
        )
        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    if user is None:
        embed_error = discord.Embed(
            title="Ошибка",
            description="Перед использованием команд вам должны добавить ник.",
            color=discord.Color(0xFF0000)
        )
        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    if not ctx.channel.id == config["guild"]["ids-list"]["channels"]["statistics"]:
        embed_error = discord.Embed(
            title="Ошибка",
            description=f"Вы не можете использовать эту команду здесь. Команда может быть использована в {channel_statistics.mention}",
            color=discord.Color(0xFF0000)
        )
        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    date_pattern = re.compile(r'^\d{2}-\d{2}-\d{4}$')

    if not date_pattern.match(start_date) or not date_pattern.match(end_date):
        embed_error = discord.Embed(title="Ошибка", description="Оба значения даты должны быть формата dd-mm-yyyy.",
                                    color=discord.Color(0xFF0000))

        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    try:
        start_date = datetime.datetime.strptime(start_date, "%d-%m-%Y").date()
        end_date = datetime.datetime.strptime(end_date, "%d-%m-%Y").date()
    except ValueError:
        embed_error = discord.Embed(title="Ошибка", description="Ошибка указанной даты.", color=discord.Color(0xFF0000))

        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    date_contract_filters = []
    date_coffers_filters = []
    date_daily_tasks_filters = []

    if start_date:
        date_contract_filters.append(Contracts.date >= start_date.strftime("%Y-%m-%d"))
        date_coffers_filters.append(Coffers.date >= start_date.strftime("%Y-%m-%d"))
        date_daily_tasks_filters.append(DailyTasks.date >= start_date.strftime("%Y-%m-%d"))
    if end_date:
        date_contract_filters.append(Contracts.date <= end_date.strftime("%Y-%m-%d"))
        date_coffers_filters.append(Coffers.date <= end_date.strftime("%Y-%m-%d"))
        date_daily_tasks_filters.append(DailyTasks.date <= end_date.strftime("%Y-%m-%d"))

    with Session() as session:
        contracts_query = session.query(Contracts.price, Contracts.reward, Contracts.status).filter(and_(*date_contract_filters))
        actions_with_coffers_query = session.query(Coffers.action, Coffers.amount).filter(and_(*date_coffers_filters))
        daily_tasks_query = session.query(DailyTasks.type_rept).filter(and_(*date_daily_tasks_filters))

    final_reward = sum(reward for price, reward, status in contracts_query.all() if status)
    final_price = sum(price for price, reward, status in contracts_query.all())

    coffers_action_take = sum(amount for action, amount in actions_with_coffers_query.all() if action == "Взял")
    coffers_action_put = sum(amount for action, amount in actions_with_coffers_query.all() if action == "Положил")

    final_daily_tasks = daily_tasks_query.filter(DailyTasks.type_rept == "Ежедневные задания").count()

    embed_title = f"Статистика за {start_date.strftime('%d-%m-%Y')}" if start_date == end_date else f"Статистика за {start_date.strftime('%d-%m-%Y')} по {end_date.strftime('%d-%m-%Y')}"

    embed = discord.Embed(title=embed_title, color=discord.Color(0xFFFFFF))
    embed.add_field(name="Куплено контрактов", value=contracts_query.count(), inline=False)
    embed.add_field(name="Выполнено контрактов", value=contracts_query.filter(Contracts.status == True).count(), inline=False)

    clean_reward = final_reward - final_price

    embed.add_field(name="Заработано с контрактов", value=f"{'{0:,}'.format(final_reward).replace(',', '.')}$ ({'{0:,}'.format(clean_reward).replace(',', '.')}$ чистых)")
    embed.add_field(name="Потрачено на контракты", value=f"{'{0:,}'.format(final_price).replace(',', '.')}$", inline=False)
    embed.add_field(name="Выполнено ежедневных заданий", value=str(final_daily_tasks), inline=False)
    embed.add_field(name="Положено на казну", value=f"{'{0:,}'.format(coffers_action_put).replace(',', '.')}$", inline=False)
    embed.add_field(name="Снято с казны", value=f"{'{0:,}'.format(coffers_action_take).replace(',', '.')}$", inline=False)

    if not contracts_query.all() and not actions_with_coffers_query.all() and not daily_tasks_query.all():
        embed_desc = f"Статистика за {start_date.strftime('%d-%m-%Y')} не найдена!" if start_date == end_date else f"Статистика за {start_date.strftime('%d-%m-%Y')} по {end_date.strftime('%d-%m-%Y')} не найдена!"
        embed_error = discord.Embed(title="Ошибка", description=embed_desc, color=discord.Color(0xFF0000))

        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    await ctx.defer()
    await ctx.respond(embed=embed)
