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


@bot.slash_command(name="отчёт", description="Отправляет отчёт, за который можно получить вознаграждение")
async def rept(ctx: discord.ApplicationContext,
               type_rept: Option(str, description="Выберите тип отправляемого отчёта", choices=["Ежедневные задания"]),
               url: Option(str, description="Загрузите скриншот о выполнении задания и приложите ссылку к отчёту")):

    with Session() as session:
        user = session.query(Users).filter_by(discord_user=ctx.author.id).first()

    channel_daily_tasks = ctx.guild.get_channel(config["guild"]["ids-list"]["channels"]["daily-tasks"])

    if ctx.channel.type == discord.ChannelType.private:
        embed_error = discord.Embed(
            title="Ошибка",
            description="Вы не можете отправлять команды боту в личные сообщения.",
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

    if not ctx.channel.id == config["guild"]["ids-list"]["channels"]["daily-tasks"]:
        embed_error = discord.Embed(
            title="Ошибка",
            description=f"Вы не можете использовать эту команду здесь. Команда может быть использована в {channel_daily_tasks.mention}",
            color=discord.Color(0xFF0000)
        )

        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    if not any(substring in url for substring in ["https://imgur.com/", "https://prnt.sc/", "https://yapx.ru/"]):
        embed_error = discord.Embed(
            title="Ошибка",
            description="Скриншоты могут быть загружены только на https://imgur.com/, https://prnt.sc/, https://yapx.ru/",
            color=discord.Color(0xFF0000)
        )

        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    try:
        with Session() as session:
            new_daily_task = DailyTasks(
                discord_user=ctx.author.id,
                type_rept=type_rept,
                url=url
            )
            session.add(new_daily_task)
            session.commit()
    except Exception as error:
        session.rollback()
        print("Произошла ошибка базы данных")
        print(error)
        embed_error = discord.Embed(
            title="Ошибка",
            description="Ошибка базы данных. Сообщите разработчику!",
            color=discord.Color(0xFF0000)
        )
        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    current_datetime = datetime.datetime.now()

    embed = discord.Embed(title=f"Новый отчёт ({type_rept})", color=discord.Color(0xFFFFFF))
    embed.add_field(name="Пользователь", value=ctx.author.mention, inline=False)
    embed.add_field(name="Ник", value=user.nickname, inline=False)
    embed.add_field(name="Дата", value=str(current_datetime.date().strftime("%d-%m-%Y")), inline=False)
    embed.add_field(name="Скриншоты", value=url, inline=False)
    embed.set_author(name=user.nickname, icon_url=ctx.author.avatar.url)
    embed.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

    await ctx.defer()
    await ctx.respond(embed=embed)
