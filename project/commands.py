import datetime
import re
import asyncio
import discord

from discord.ext import commands
from discord.commands import Option
from project import bot, contracts, engine, Base, Session, tasks, config, admin_roles
from project.models import Contracts, Coffers, DailyTasks, Users, Warehouse
from sqlalchemy import cast, Date, or_, and_
from project.functions import is_owner, cron_send_statistics

contract_choices = [contract["name"] for contract in contracts]

@bot.slash_command(name="объявление", description="Отправляет объявление всем участникам сообщества.")
async def collection(ctx: discord.ApplicationContext, *, message: str):
    with Session() as session:
        user = session.query(Users).filter_by(discord_user=ctx.author.id).first()

    channel_ads = ctx.guild.get_channel(config["guild"]["ids-list"]["channels"]["ads"])
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

    if not ctx.channel_id == config["guild"]["ids-list"]["channels"]["ads"]:
        embed_error = discord.Embed(
            title="Ошибка",
            description=f"Вы не можете использовать эту команду здесь. Команда может быть использована в {channel_ads.mention}",
            color=discord.Color(0xFF0000)
        )
        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    embed = discord.Embed(
        title="Новое объявление",
        description=message,
        color=discord.Color(0xFFFFFF)
    )
    embed.set_thumbnail(url=bot.user.avatar.url)
    embed.set_author(name=user.nickname, icon_url=ctx.author.avatar.url)
    embed.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

    embed_success = discord.Embed(
        title="Успешно",
        description="Вы успешно сообщили о сборе.",
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

    await channel.send(role_member.mention, embed=embed)
    await ctx.respond(embed=embed_success, ephemeral=True)
    await asyncio.gather(*tasks)


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

    if not ctx.channel_id == config["guild"]["ids-list"]["channels"]["contracts"]:
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
            description=f"Пользователь {user.nickname} взял контракт {contract}. Зайдите в игру и выполните условия контракта",
            color=0xFFFFFF
        )

        embed_success = discord.Embed(
            title="Успешно",
            description=f"Вы успешно взяли контракт {contract}",
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

    if not ctx.channel_id == config["guild"]["ids-list"]["channels"]["warehouse"]:
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


@bot.slash_command(name="казна", description="Отправляет отчётность по казне")
async def coffers(ctx: discord.ApplicationContext,
                  action: Option(str, description="Выберите действие, которое было произведено с деньгами", choices=["Взял", "Положил"]),
                  *, amount: Option(int, description="Укажите сумму, с которой была произведена операция")):

    with Session() as session:
        user = session.query(Users).filter_by(discord_user=ctx.author.id).first()

    channel_coffers = ctx.guild.get_channel(config["guild"]["ids-list"]["channels"]["coffers"])

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

    if not ctx.channel_id == config["guild"]["ids-list"]["channels"]["coffers"]:
        embed_error = discord.Embed(
            title="Ошибка",
            description=f"Вы не можете использовать эту команду здесь. Команда может быть использована в {channel_coffers.mention}",
            color=discord.Color(0xFF0000)
        )
        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    if amount <= 0 and amount < 1000000000:
        embed_error = discord.Embed(
            title="Ошибка",
            description="Вы не можете указать цифру 0 или меньше 0, а также, больше 1.000.000.000",
            color=discord.Color(0xFF0000)
        )
        await ctx.defer(ephemeral=True)
        return await ctx.respond(embed=embed_error, ephemeral=True)

    try:
        with Session() as session:
            new_action = Coffers(
                discord_user=ctx.author.id,
                action=action,
                amount=amount
            )
            session.add(new_action)
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

    embed_coffers = discord.Embed(
        title="Отчётность по казне",
        color=discord.Color(0xFFFFFF)
    )
    embed_coffers.add_field(name="Пользователь", value=ctx.author.mention, inline=False)
    embed_coffers.add_field(name="Ник", value=user.nickname, inline=False)
    embed_coffers.add_field(name="Действие", value=action, inline=False)
    embed_coffers.add_field(name="Сумма денег", value=f"{'{0:,}'.format(amount).replace(',', '.')}$", inline=False)
    embed_coffers.set_author(name=user.nickname, icon_url=ctx.author.avatar.url)
    embed_coffers.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

    embed_coffers.timestamp = datetime.datetime.now()

    await ctx.defer()
    await ctx.respond(embed=embed_coffers)


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

    if not ctx.channel_id == config["guild"]["ids-list"]["channels"]["daily-tasks"]:
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


@bot.slash_command(name="участник", description="Позволяет добавить или удалить ник участнику")
async def member_cmd(ctx: discord.ApplicationContext,
                 action: Option(str, description="Выберите действие с указанным участником", choices=["Добавить", "Удалить", "Изменить", "Информация"]),
                 member: discord.Member,
                 *, nickname=None):

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

    if not ctx.channel_id == config["guild"]["ids-list"]["channels"]["commands"]:
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
                        nickname=nickname
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
        if nickname:
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

            try:
                with Session() as session:
                    user.nickname = nickname
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

            embed_success = discord.Embed(
                title="Успешно",
                description=f"Ник пользователя {member.mention} был изменён на **{nickname}**.",
                color=discord.Color(0x18B542)
            )
            await ctx.defer()
            await ctx.respond(embed=embed_success)
        else:
            embed_error = discord.Embed(
                title="Ошибка",
                description=f"При изменении пользователя вы должны указать новый ник.",
                color=discord.Color(0xFF0000)
            )
            await ctx.defer(ephemeral=True)
            return await ctx.respond(embed=embed_error, ephemeral=True)

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
        embed_success.add_field(name="Дискорд ID", value=f"{member.id}", inline=False)
        embed_success.add_field(name="Выполненно ежедневных заданий", value=user_daily_tasks, inline=False)
        embed_success.add_field(name="Дата добавления", value=f"{user.date.strftime('%d-%m-%Y')}", inline=False)

        await ctx.defer()
        await ctx.respond(embed=embed_success)


@bot.slash_command(name="статистика", description="Выводит статистику бота")
async def statistic(ctx: discord.ApplicationContext,
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

    if not ctx.channel_id == config["guild"]["ids-list"]["channels"]["statistics"]:
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
    except ValueError as error:
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


@bot.slash_command(name="пинг", description="Показывает пинг бота")
async def ping(ctx: discord.ApplicationContext):
    current_time = datetime.datetime.now()
    uptime = current_time - bot.start_time
    hours = uptime.total_seconds() // 3600

    db_start_time = datetime.datetime.now()

    with Session() as session:
        session.query(Users).first()

    db_stop_time = datetime.datetime.now()

    query_time = (db_stop_time - db_start_time).total_seconds() * 1000

    embed = discord.Embed(color=discord.Color(0x18B542))
    embed.add_field(name="Время отклика бота", value=f"{round(bot.latency * 1000)} мс.", inline=False)
    embed.add_field(name="Время отклика БД", value=f"{query_time:.0f} мс.", inline=False)
    embed.add_field(name="Аптайм (время работы)", value=f"{int(hours)} часов {int(uptime.seconds/60)%60} минут", inline=False)
    embed.add_field(name="Версия бота", value=bot.version, inline=False)
    embed.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

    await ctx.defer(ephemeral=True)
    await ctx.respond(embed=embed, ephemeral=True)


@commands.check(is_owner)
@bot.command(name="clear")
async def delete_messages(ctx: discord.ApplicationContext, amount: int):
    await ctx.channel.purge(limit=amount + 1)


@commands.check(is_owner)
@bot.command(name="embed")
async def embed_message(ctx: discord.ApplicationContext, content, *, message: str):
    if content == "-":
        content = ""

    lines = message.split('\n')
    title = lines[0]
    description = '\n'.join(lines[1:])

    embed = discord.Embed(
        title=title,
        color=discord.Color(0xFFFFFF),
        description=description
    )

    embed.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

    await ctx.message.delete()
    await ctx.send(content, embed=embed)


@commands.check(is_owner)
@bot.command(name="info")
async def db(ctx: discord.ApplicationContext):
    channel = ctx.guild.get_channel(1107937278363455518)
    contracts_info = ""

    for contract in contracts:
        contracts_info += f"- {contract['name']}. Описание: {contract['description']}\n"

    embed_info_1 = discord.Embed(
        title="Общая информация",
        description=f"Сообщества — грубо говоря это организации, которые могут создавать игроки, набирая своих людей и руководя "
                    "сообществом. Можно сказать, что сообщество — это семья. Сообщества бывают двух видов:\n- Крайм\n- Гос\n"
                    "Сообщество WestCompany имеет направление Крайм. Вид сообщества влияет на доступные задания. Так-же есть контракты. "
                    "Всего их 4 вида, за выполнение которых участник, который принимал участие в закрытии контракта, "
                    "получает определённое кол-во купонов, которые являются дополнительной валютой между игроками, а так-же за них можно "
                    "покупать эксклюзивную одежду в эксклюзивном магазине. Помимо контрактов в сообществе есть персональные задания, "
                    "которые могут выполнять участники сообщества каждые 24 часа, получая за это денежное вознаграждение и купоны. "
                    "Помимо системных подарков за выполнение заданий и контрактов, участники сообщества получают так-же премии за активность "
                    "внутри семьи.",
        color=discord.Color(0xFFFFFF)
    )
    embed_info_1.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)
    embed_info_1.set_thumbnail(url=bot.user.avatar.url)

    embed_info_2 = discord.Embed(
        title="Контракты",
        description="Контракты — это задания. Отличие от ежедневных заданий: контракт покупает человек, у которого есть такие полномочия. "
                    "За выполнение задания сообщество получает деньги и опыт, а участник сообщества, который учавствовал в "
                    "закрытии контракта, получает определённое количество купонов (за каждый контракт по разному). "
                    f"Всего есть 4 вида контрактов:\n{contracts_info}Если на данном этапе вам не понятно, что нужно делать, "
                    "то ничего страшного. При взятии контракта новичкам помогают в их выполнении.",
        color=discord.Color(0xFFFFFF)
    )
    embed_info_2.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)
    embed_info_2.set_thumbnail(url=bot.user.avatar.url)

    embed_info_3 = discord.Embed(
        title="Система повышения рангов",
        description="Повышение ранга в сообществе построено на активности (то есть выполнении ежедневных заданий). "
                    "Каждый день участник может выполнить 2 ежедневных задания, получив в сумме 125 очков активности. "
                    "Систематически выполняя ежедневные задания, участник будет получать очки активности, за которые сможет повышать свой ранг. "
                    "Повышение ранга позволяет получать более высокие премии, брать лучшие автомобили с гаража, "
                    "пользоваться недоступным на низких рангах функционалом (склад, казна и т.п)",
        color=discord.Color(0xFFFFFF)
    )

    embed_info_3.add_field(name="[1] Подданый — [2] Стратег", value="125 очков активности", inline=False)
    embed_info_3.add_field(name="[2] Стратег — [3] Сокрушитель", value="250 очков активности", inline=False)
    embed_info_3.add_field(name="[3] Сокрушитель — [4] Ветеран", value="375 очков активности", inline=False)
    embed_info_3.add_field(name="[4] Ветеран — [5] Элита", value="500 очков активности", inline=False)
    embed_info_3.add_field(name="[5] Элита — [6] Зам. Менеджера", value="625 очков активности\nДоверие хайрангов", inline=False)
    embed_info_3.add_field(name="[6] Зам. Менеджера — [7] Менеджер", value="750 очков активности\nДоверие хайрангов", inline=False)
    embed_info_3.add_field(name="[7] Менеджер — [8] Управляющий", value="1.000 очков активности\nДоверие хайрангов\nДоверие от лидера", inline=False)

    embed_info_3.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)
    embed_info_3.set_thumbnail(url=bot.user.avatar.url)

    embed_info_4 = discord.Embed(
        title="Зарплаты и премии",
        description="За выполнение ежедневных заданий, участник сообщества вознаграждается премией в конце недели. "
                    "Для получение премии участник должен оставлять отчёты о выполнении ежедвневных заданий в специальном канале <#1154735367157727274> "
                    "Бот подсчитывает премии в конце недели, взяв во внимание все отчёты о выполнении ежедневных заданий. "
                    "Отчёты перепроверяются хайрангами сообщества, после чего деньги выплачиваются участникам.",
        color=discord.Color(0xFFFFFF)
    )

    embed_info_4.add_field(name="Денежные выплаты", value="Выполнение ежедневного задания (1 шт.) — 75.000$\n"
                                                          "Выполнение ежедневных заданий (2 шт.) — 150.000$")

    embed_info_4.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)
    embed_info_4.set_thumbnail(url=bot.user.avatar.url)

    await ctx.message.delete()
    await channel.send(embeds=[embed_info_1, embed_info_2, embed_info_3, embed_info_4])
