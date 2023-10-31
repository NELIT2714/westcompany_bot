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


@bot.slash_command(name="участник", description="Позволяет добавить или удалить ник участнику")
async def member_cmd(ctx: discord.ApplicationContext,
                     action: Option(str, description="Выберите действие с указанным участником", choices=["Добавить", "Удалить", "Изменить", "Информация"]),
                     member: discord.Member,
                     *, nickname=None,
                     bank_account: int=None):

    with Session() as session:
        user = session.query(Users).filter_by(discord_user=ctx.author.id).first()

    commands_channel = ctx.guild.get_channel(config["guild"]["ids-list"]["channels"]["commands"])
    member_role = ctx.guild.get_role(config["guild"]["ids-list"]["roles"]["member"])

    if member == bot.user:
        embed_error = discord.Embed(
            title="Ошибка",
            description=f"Ошибка пользователя! Вы не можете выбрать {bot.user.mention}",
            color=discord.Color(0xFF0000)
        )
        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    if ctx.channel.type == discord.ChannelType.private:
        embed_error = discord.Embed(
            title="Ошибка",
            description="Вы не можете отправлять команды боту в личные сообщения.",
            color=discord.Color(0xFF0000)
        )
        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    if not any(admin_role.id in admin_roles for admin_role in ctx.author.roles):
        if member.id == 463277343150964738 and not ctx.author.id == 463277343150964738:
            embed_error = discord.Embed(
                title="Ошибка",
                description="У вас нет прав",
                color=discord.Color(0xFF0000)
            )
            await ctx.defer(ephemeral=True)
            return await ctx.respond(embed=embed_error, ephemeral=True)

    if user is None and not is_owner(ctx):
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
            description=f"Вы не можете использовать эту команду здесь. Команда может быть использована в {commands_channel.mention}",
            color=discord.Color(0xFF0000)
        )
        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    if nickname:
        nickname = " ".join(nickname.split())
        nickname = nickname.replace("_", " ")

    if action == "Добавить":
        if nickname:
            if bank_account:
                with Session() as session:
                    user = session.query(Users).filter_by(discord_user=member.id).first()

                if user is not None:
                    embed_error = discord.Embed(
                        title="Ошибка",
                        description=f"Такой пользователь уже есть в базе данных и имеет никнейм **{user.nickname}**",
                        color=discord.Color(0xFF0000)
                    )
                    await ctx.defer(ephemeral=True)
                    return await ctx.respond(embed=embed_error, ephemeral=True)

                try:
                    with Session() as session:
                        new_user = Users(
                            discord_user=member.id,
                            nickname=nickname,
                            bank_account=bank_account
                        )
                        session.add(new_user)
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

                await member.add_roles(member_role)

                try:
                    await member.edit(nick=nickname)
                except Exception as error:
                    print(error)

                embed_success = discord.Embed(
                    title="Успешно",
                    description=f"Пользователь {member.mention} был успешно добавлен под ником **{nickname}**",
                    color=discord.Color(0x18B542)
                )
                await ctx.defer()
                await ctx.respond(embed=embed_success)
            else:
                embed_error = discord.Embed(
                    title="Ошибка",
                    description=f"При добавлении пользователя вы должны банковский счёт.",
                    color=discord.Color(0xFF0000)
                )
                await ctx.defer(ephemeral=True)
                return await ctx.respond(embed=embed_error, ephemeral=True)
        else:
            embed_error = discord.Embed(
                title="Ошибка",
                description=f"При добавлении пользователя вы должны указать ник.",
                color=discord.Color(0xFF0000)
            )
            await ctx.defer(ephemeral=True)
            return await ctx.respond(embed=embed_error, ephemeral=True)

    elif action == "Удалить":
        with Session() as session:
            user = session.query(Users).filter_by(discord_user=member.id).first()

        if user is None:
            embed_error = discord.Embed(
                title="Ошибка",
                description=f"Невозможно удалить пользователя {member.mention}, так как он ещё не был добавлен.",
                color=discord.Color(0xFF0000)
            )
            await ctx.defer(ephemeral=True)
            return await ctx.respond(embed=embed_error, ephemeral=True)

        try:
            with Session() as session:
                session.query(Users).filter_by(discord_user=member.id).delete()
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

        for role in member.roles:
            if not role.name == "@everyone":
                await member.remove_roles(role)

        try:
            await member.edit(nick=None)
        except Exception as error:
            print(error)

        embed_success = discord.Embed(
            title="Успешно",
            description=f"Пользователь {member.mention} был удалён.",
            color=discord.Color(0x18B542)
        )
        await ctx.defer()
        await ctx.respond(embed=embed_success)

    elif action == "Изменить":
        with Session() as session:
            user = session.query(Users).filter_by(discord_user=member.id).first()

        if user is None:
            embed_error = discord.Embed(
                title="Ошибка",
                description=f"Невозможно изменить ник пользователю {member.mention}, так как он ещё не был добавлен.",
                color=discord.Color(0xFF0000)
            )
            await ctx.defer(ephemeral=True)
            return await ctx.respond(embed=embed_error, ephemeral=True)

        if not bank_account and not nickname:
            embed_error = discord.Embed(
                title="Ошибка",
                description=f"Для изменения пользователя {member.mention} вы должны указать новый банковский счёт или никнейм.",
                color=discord.Color(0xFF0000)
            )
            await ctx.defer(ephemeral=True)
            return await ctx.respond(embed=embed_error, ephemeral=True)

        try:
            with Session() as session:
                if nickname:
                    user.nickname = nickname
                if bank_account:
                    user.bank_account = bank_account
                session.add(user)
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

        try:
            await member.edit(nick=nickname)
        except Exception as error:
            print(error)

        add_desc = ""

        if bank_account and not nickname:
            add_desc = f"Новый банковский счёт: **{bank_account}**"
        elif nickname and not bank_account:
            add_desc = f"Новый ник: **{nickname}**"
        elif nickname and bank_account:
            add_desc = f"Новый ник: **{nickname}**. Новый банковский счёт: **{bank_account}**"

        embed_success = discord.Embed(
            title="Успешно",
            description=f"Пользователь {member.mention} был изменён.\n{add_desc}",
            color=discord.Color(0x18B542)
        )
        await ctx.defer()
        await ctx.respond(embed=embed_success)

    elif action == "Информация":
        with Session() as session:
            user = session.query(Users).filter_by(discord_user=member.id).first()

        if user is None:
            embed_error = discord.Embed(
                title="Ошибка",
                description=f"Невозможно посмотреть информацию о пользователе {member.mention}, так как он ещё не был добавлен.",
                color=discord.Color(0xFF0000)
            )
            await ctx.defer(ephemeral=True)
            return await ctx.respond(embed=embed_error, ephemeral=True)

        with Session() as session:
            user_daily_tasks = session.query(DailyTasks).filter_by(discord_user=member.id).count()

        embed_success = discord.Embed(
            title=f"Информация об участнике {user.nickname}",
            color=discord.Color(0xFFFFFF)
        )
        embed_success.add_field(name="Пользователь", value=f"{member.mention}", inline=False)
        embed_success.add_field(name="Ник", value=f"{user.nickname}", inline=False)
        embed_success.add_field(name="Банковский счёт", value=f"{user.bank_account}", inline=False)
        embed_success.add_field(name="Дискорд ID", value=f"{member.id}", inline=False)
        embed_success.add_field(name="Выполненно ежедневных заданий", value=user_daily_tasks, inline=False)
        embed_success.add_field(name="Дата добавления", value=f"{user.date.strftime('%d-%m-%Y')}", inline=False)

        await ctx.defer()
        await ctx.respond(embed=embed_success)
