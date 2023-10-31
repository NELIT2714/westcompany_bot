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


@bot.command(name="участник-инфо")
async def member_info(ctx: discord.ApplicationContext, user, start_date=None, end_date=None):
    channel_commands = ctx.guild.get_channel(config["guild"]["ids-list"]["channels"]["commands"])

    if not any(admin_role.id in admin_roles for admin_role in ctx.author.roles):
        return

    if not ctx.channel.id == config["guild"]["ids-list"]["channels"]["commands"]:
        embed_error = discord.Embed(
            title="Ошибка",
            description=f"Вы не можете использовать эту команду здесь. Команда может быть использована в {channel_commands.mention}",
            color=discord.Color(0xFF0000)
        )
        return await ctx.send(ctx.author.mention, embed=embed_error)

    try:
        member = await commands.MemberConverter().convert(ctx, user)
    except commands.MemberNotFound:
        try:
            member = await bot.fetch_user(user)
        except Exception:
            embed_error = discord.Embed(
                title="Ошибка",
                description="Пользователь не найден.",
                color=discord.Color(0xFF0000)
            )
            return await ctx.send(ctx.author.mention, embed=embed_error)

    if start_date and end_date:
        date_pattern = re.compile(r'^\d{2}-\d{2}-\d{4}$')

        if not date_pattern.match(start_date) or not date_pattern.match(end_date):
            embed_error = discord.Embed(title="Ошибка", description="Оба значения даты должны быть формата dd-mm-yyyy.",
                                        color=discord.Color(0xFF0000))

            return await ctx.send(embed=embed_error)

        try:
            start_date = datetime.datetime.strptime(start_date, "%d-%m-%Y").date()
            end_date = datetime.datetime.strptime(end_date, "%d-%m-%Y").date()
        except ValueError:
            embed_error = discord.Embed(title="Ошибка", description="Ошибка указанной даты.", color=discord.Color(0xFF0000))
            return await ctx.send(embed=embed_error)

    with Session() as session:
        user = session.query(Users).filter_by(discord_user=member.id).first()

    if user is None:
        embed_error = discord.Embed(
            title="Ошибка",
            description=f"Пользователь {member.mention} ({member.id}) не добавлен в базу участников сообщества.",
            color=discord.Color(0xFF0000)
        )

        return await ctx.send(embed=embed_error)

    with Session() as session:
        daily_tasks_all = session.query(DailyTasks).filter_by(discord_user=member.id).count()

        if start_date and end_date:
            daily_tasks_filtered = session.query(DailyTasks).filter(
                DailyTasks.date >= start_date).filter(
                DailyTasks.date <= end_date
            ).filter_by(discord_user=member.id).count()

    user_info_embed = discord.Embed(
        title=f"Профиль пользователя {user.nickname}",
        color=discord.Color(0xFFFFFF)
    )
    user_info_embed.add_field(name="Пользователь", value=member.mention, inline=True)
    user_info_embed.add_field(name="Ник", value=user.nickname, inline=True)
    user_info_embed.add_field(name="Дискорд ID", value=member.id, inline=False)
    user_info_embed.add_field(name="Дата регистрация", value=format_dt(member.created_at, "D"), inline=True)

    if member in ctx.guild.members:
        user_info_embed.add_field(name="Дата присоединения", value=format_dt(member.joined_at, "D"), inline=True)

    user_info_embed.add_field(name="Всего выполнено ежедневных заданий", value=daily_tasks_all, inline=False)

    if start_date and end_date:
        user_info_embed.add_field(name=f"Выполнено заданий за период ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})", value=daily_tasks_filtered, inline=False)

    user_info_embed.add_field(name="Всего заработано", value=f'≈ {"{0:,}".format(daily_tasks_all * int(config["other"]["salary"]["daily-task"])).replace(",", ".")}$', inline=False)

    if start_date and end_date:
        user_info_embed.add_field(name=f"Заработано за период ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})", value=f'≈ {"{0:,}".format(daily_tasks_filtered * int(config["other"]["salary"]["daily-task"])).replace(",", ".")}$', inline=False)

    try:
        user_info_embed.set_thumbnail(url=member.avatar.url)
    except:
        user_info_embed.set_thumbnail(url=bot.user.avatar.url)

    user_info_embed.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

    await ctx.send(ctx.author.mention, embed=user_info_embed)

@member_info.error
async def member_info_error(ctx, error):
    channel_commands = ctx.guild.get_channel(config["guild"]["ids-list"]["channels"]["commands"])
    if not ctx.channel.id == config["guild"]["ids-list"]["channels"]["commands"]:
        embed_error = discord.Embed(
            title="Ошибка",
            description=f"Вы не можете использовать эту команду здесь. Команда может быть использована в {channel_commands.mention}",
            color=discord.Color(0xFF0000)
        )
        return await ctx.send(ctx.author.mention, embed=embed_error)

    if isinstance(error, commands.MissingRequiredArgument):
        embed_used = discord.Embed(
            title="Использование команды",
            description="Использование команды:\n- /участник-инфо (Упоминание @ / Discord ID) (start_date) (end_date)\nПараметры start_date и end_date — необязательны для заполнения. Если начальная и конечная дата не указаны, то будет выведена общая информация о пользователе. Информация за указанный промежуток времени будет показана только при наличии необязательных параметров.",
            color=discord.Color(0xFFC800)
        )
        embed_used.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)
        await ctx.send(ctx.author.mention, embed=embed_used)
