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


contract_choices = [contract["name"] for contract in contracts]

@bot.slash_command(name="контракт", description="Заполнение информации о контракте")
async def contract(ctx: discord.ApplicationContext,
                   contract: Option(str, description="Выберите тип контракта", choices=contract_choices),
                   status: Option(str, description="Выберите статус контракта", choices=["Выполнен", "Не выполнен", "Взят (в процессе выполнения)"])):

    with Session() as session:
        user = session.query(Users).filter_by(discord_user=ctx.author.id).first()

    channel_contracts = ctx.guild.get_channel(config["guild"]["ids-list"]["channels"]["contracts"])

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

    if not ctx.channel.id == config["guild"]["ids-list"]["channels"]["contracts"]:
        embed_error = discord.Embed(
            title="Ошибка",
            description=f"Вы не можете использовать эту команду здесь. Команда может быть использована в {channel_contracts.mention}",
            color=discord.Color(0xFF0000)
        )
        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    found_contract_info = None

    for contract_info in contracts:
        if contract_info["name"] == contract:
            found_contract_info = contract_info
            break

    if status == "Выполнен":
        try:
            with Session() as session:
                new_contract = Contracts(
                    contract_name=contract,
                    discord_user=ctx.author.id,
                    price=int(found_contract_info["price"]),
                    reward=int(found_contract_info["reward"]),
                    status=True
                )
                session.add(new_contract)
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

        embed_success = discord.Embed(
            title=f"Новый контракт",
            description=f'Контракт "{contract}" был успешно выполнен!',
            color=discord.Color(0xFFFFFF)
        )

        embed_success.add_field(name="Контракт", value=contract, inline=False)
        embed_success.add_field(name="Цена контракта",
                                value=f"{'{0:,}'.format(found_contract_info['price']).replace(',', '.')}$",
                                inline=False)
        embed_success.add_field(name="Награда за выполнение",
                                value=f"{'{0:,}'.format(found_contract_info['reward']).replace(',', '.')}$",
                                inline=False)
        embed_success.set_author(name=user.nickname, icon_url=ctx.author.avatar.url)
        embed_success.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

        await ctx.defer()
        await ctx.respond(embed=embed_success)
    elif status == "Не выполнен":
        try:
            new_contract = Contracts(
                contract_name=contract,
                discord_user=ctx.author.id,
                price=int(found_contract_info["price"]),
                reward=int(found_contract_info["reward"]),
                status=False
            )
            session.add(new_contract)
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

        embed_fail = discord.Embed(
            title=f"Новый контракт",
            description=f'Контракт "{contract}" не был выполнен!',
            color=discord.Color(0xFFFFFF),
        )

        embed_fail.add_field(name="Контракт", value=contract, inline=False)
        embed_fail.add_field(name="Цена контракта",
                             value=f"{'{0:,}'.format(found_contract_info['price']).replace(',', '.')}$",
                             inline=False)
        embed_fail.set_author(name=user.nickname, icon_url=ctx.author.avatar.url)
        embed_fail.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

        await ctx.defer()
        await ctx.respond(embed=embed_fail)
    elif "Взят (в процессе выполнения)":
        channel_ads = ctx.guild.get_channel(config["guild"]["ids-list"]["channels"]["ads"])
        role_member = ctx.guild.get_role(config["guild"]["ids-list"]["roles"]["member"])

        embed = discord.Embed(
            title="Взят новый контракт",
            description=f"Контракт «{contract}» куплен. Зайдите в игру и выполните условия контракта",
            color=0xFFFFFF
        )

        embed_success = discord.Embed(
            title="Успешно",
            description=f"Вы успешно взяли контракт «{contract}»",
            color=discord.Color(0x18B542)
        )

        embed.set_author(name=user.nickname, icon_url=ctx.author.avatar.url)
        embed.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)
        embed.set_thumbnail(url=bot.user.avatar.url)

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
