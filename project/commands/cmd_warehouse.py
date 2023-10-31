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


@bot.slash_command(name="склад", description="Отправляет отчётность по складу")
async def warehouse(ctx: discord.ApplicationContext,
                    action: Option(str, description="Выберите действие, которое было произведено с предметом", choices=["Взял", "Положил"]),
                    *, item: Option(str, description="Укажите название передмета/предметов")):

    with Session() as session:
        user = session.query(Users).filter_by(discord_user=ctx.author.id).first()

    channel_warehouse = ctx.guild.get_channel(config["guild"]["ids-list"]["channels"]["warehouse"])

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

    if not ctx.channel.id == config["guild"]["ids-list"]["channels"]["warehouse"]:
        embed_error = discord.Embed(
            title="Ошибка",
            description=f"Вы не можете использовать эту команду здесь. Команда может быть использована в {channel_warehouse.mention}",
            color=discord.Color(0xFF0000)
        )
        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    try:
        with Session() as session:
            warehouse_object = Warehouse(
                discord_user=ctx.author.id,
                action=action,
                item=item
            )
            session.add(warehouse_object)
            session.commit()
    except Exception as error:
        session.rollback()
        print("Произошла ошибка базы данных!")
        print(error)
        embed_error = discord.Embed(
            title="Ошибка",
            description="Ошибка базы данных. Сообщите разработчику!",
            color=discord.Color(0xFF0000)
        )
        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    embed_warehouse = discord.Embed(
        title="Отчётность по складу",
        color=discord.Color(0xFFFFFF)
    )
    embed_warehouse.add_field(name="Пользователь", value=ctx.author.mention, inline=False)
    embed_warehouse.add_field(name="Ник", value=user.nickname, inline=False)
    embed_warehouse.add_field(name="Действие", value=action, inline=False)
    embed_warehouse.add_field(name="Передмет/предметы", value=item, inline=False)
    embed_warehouse.set_author(name=user.nickname, icon_url=ctx.author.avatar.url)
    embed_warehouse.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

    embed_warehouse.timestamp = datetime.datetime.now()

    await ctx.defer()
    await ctx.respond(embed=embed_warehouse)
