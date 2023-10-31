import datetime
import asyncio
import discord
import re

from discord.ext import commands
from discord.commands import Option
from discord.utils import format_dt

from project import bot, contracts, Base, Session, tasks, config, admin_roles
from project.models import Contracts, Coffers, DailyTasks, Users, Warehouse
from project.functions import is_owner, cron_send_statistics

from sqlalchemy import cast, Date, or_, and_


@bot.slash_command(name="профиль", description="Профиль пользователя")
async def profile(ctx: discord.ApplicationContext):
    start_of_week = datetime.datetime.now() - datetime.timedelta(days=datetime.datetime.now().weekday())

    with Session() as session:
        user = session.query(Users).filter_by(discord_user=ctx.author.id).first()

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
            description="Ваш профиль не найден. Вы не добавлены в список участников сообщества",
            color=discord.Color(0xFF0000)
        )
        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    with Session() as session:
        daily_tasks_all = session.query(DailyTasks).filter_by(discord_user=ctx.author.id).count()

        daily_tasks_week = session.query(DailyTasks).filter(
            DailyTasks.date >= start_of_week.date()).filter(
            DailyTasks.date <= datetime.datetime.now().date()
        ).filter_by(discord_user=ctx.author.id).count()

    profile_embed = discord.Embed(
        title=f"Профиль пользователя {user.nickname}",
        color=discord.Color(0xFFFFFF)
    )
    profile_embed.add_field(name="Пользователь", value=ctx.author.mention, inline=True)
    profile_embed.add_field(name="Ник", value=user.nickname, inline=True)
    profile_embed.add_field(name="Дискорд ID", value=ctx.author.id, inline=False)
    profile_embed.add_field(name="Дата регистрация", value=format_dt(ctx.author.created_at, "D"), inline=True)
    profile_embed.add_field(name="Дата присоединения", value=format_dt(ctx.author.joined_at, "D"), inline=True)
    profile_embed.add_field(name="Всего выполнено ежедневных заданий", value=daily_tasks_all, inline=False)
    profile_embed.add_field(name=f"Выполнено ежд. заданий за период ({start_of_week.strftime('%d.%m')} - {datetime.datetime.now().strftime('%d.%m')})", value=daily_tasks_week, inline=False)
    profile_embed.add_field(name="Всего заработано", value=f'≈ {"{0:,}".format(daily_tasks_all * int(config["other"]["salary"]["daily-task"])).replace(",", ".")}$', inline=False)
    profile_embed.add_field(name=f"Заработано за период ({start_of_week.strftime('%d.%m')} - {datetime.datetime.now().strftime('%d.%m')})", value=f'≈ {"{0:,}".format(daily_tasks_week * int(config["other"]["salary"]["daily-task"])).replace(",", ".")}$', inline=False)

    profile_embed.set_thumbnail(url=ctx.author.avatar.url)
    profile_embed.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

    await ctx.defer(ephemeral=True)
    await ctx.respond(embed=profile_embed, ephemeral=True)
