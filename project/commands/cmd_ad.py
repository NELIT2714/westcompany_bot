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


@bot.slash_command(name="объявление", description="Отправляет объявление всем участникам сообщества.")
async def ad(ctx: discord.ApplicationContext, *, message: str):
    with Session() as session:
        user = session.query(Users).filter_by(discord_user=ctx.author.id).first()

    channel_ads = ctx.guild.get_channel(config["guild"]["ids-list"]["channels"]["ads"])
    channel_commands = ctx.guild.get_channel(config["guild"]["ids-list"]["channels"]["commands"])

    role_member = ctx.guild.get_role(config["guild"]["ids-list"]["roles"]["member"])

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

    if not ctx.channel.id == config["guild"]["ids-list"]["channels"]["commands"]:
        embed_error = discord.Embed(
            title="Ошибка",
            description=f"Вы не можете использовать эту команду здесь. Команда может быть использована в {channel_commands.mention}",
            color=discord.Color(0xFF0000)
        )
        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    embed = discord.Embed(
        title="Новое объявление",
        description=f"Пользователь {user.nickname} отправил объявление для участников сообщества.\n**Сообщение:** {message}",
        color=discord.Color(0xFFFFFF)
    )
    embed.set_thumbnail(url=bot.user.avatar.url)
    embed.set_author(name=user.nickname, icon_url=ctx.author.avatar.url)
    embed.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

    embed_success = discord.Embed(
        title="Успешно",
        description="Вы успешно отправили объявление.",
        color=discord.Color(0x18B542)
    )

    await ctx.defer(ephemeral=True)

    for member in ctx.guild.members:
        if not member == bot.user and role_member in member.roles:
            try:
                tasks.append(member.send(embed=embed))
            except discord.Forbidden:
                pass
        else:
            continue

    await channel_ads.send(role_member.mention, embed=embed)
    await ctx.respond(embed=embed_success, ephemeral=True)
    await asyncio.gather(*tasks)
