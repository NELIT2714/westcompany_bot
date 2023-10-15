import discord
import datetime

from project import bot, contracts, engine, Base, Session, config, admin_roles
from project.models import Contracts, Coffers, DailyTasks, Users

from sqlalchemy import cast, Date, or_, and_


@bot.event
async def on_ready():
    bot.start_time = datetime.datetime.now()
    Base.metadata.create_all(engine)
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(name=config["bot"]["activity"])
    )
    print(f"Logged in as {bot.user.name} | ID: {bot.user.id}")


@bot.event
async def on_member_join(member):
    guest_role = discord.utils.get(member.guild.roles, id=config["guild"]["ids-list"]["roles"]["guest"])
    channel = member.guild.get_channel(config["guild"]["ids-list"]["channels"]["greetings"])

    embed_after_join = discord.Embed(
        title="Новый участник",
        description=f"Приветствуем нового пользователя {member.mention} на Discord сервере сообщества WestCompany.\
                    \Мы рады каждому, кто присоединился к нам. Узнать подробнее о сообществе можно в канале <#1107937278363455518>",
        color=discord.Color(0xFFFFFF)
    )
    embed_after_join.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)
    embed_after_join.set_thumbnail(url=bot.user.avatar.url)

    await member.add_roles(guest_role)
    await channel.send(f"{member.mention}", embed=embed_after_join)

    with Session() as session:
        user = session.query(Users).filter_by(discord_user=member.id).first()

    if not user is None:
        member_role = discord.utils.get(member.guild.roles, id=config["guild"]["ids-list"]["roles"]["member"])

        await member.add_roles(member_role)
        await member.edit(nick=user.nickname)

@bot.event
async def on_member_update(before, after):
    guest_role = discord.utils.get(after.guild.roles, id=config["guild"]["ids-list"]["roles"]["guest"])
    member_role = discord.utils.get(after.guild.roles, id=config["guild"]["ids-list"]["roles"]["member"])
    highrank = discord.utils.get(after.guild.roles, id=config["guild"]["ids-list"]["roles"]["highrank"])

    if member_role in after.roles:
        with Session() as session:
            user = session.query(Users).filter_by(discord_user=after.id).first()

        if user is None:
            embed_error = discord.Embed(
                title="Ошибка",
                description="Вам попытались выдать роль Участник сообщества. Однако, вам не добавили ник через команду /участник.",
                color=discord.Color(0xFF0000)
            )
            await after.remove_roles(member_role)
            await after.send(embed=embed_error)

    for admin_role in admin_roles:
        role = discord.utils.get(after.guild.roles, id=admin_role)
        if role in after.roles:
            await after.add_roles(highrank)
            break
        else:
            continue

    if len(after.roles) == 1 and not guest_role in after.roles:
        await after.add_roles(guest_role)
    elif len(after.roles) > 2 and guest_role in after.roles:
        await after.remove_roles(guest_role)


#@bot.event
#async def on_presence_update(before, after):
#    channel = bot.get_channel(1108132947598512218)
#    nelit_id = 463277343150964738
#
#    if after.id == nelit_id:
#        if after.status == discord.Status.online or after.status == discord.Status.dnd or after.status == discord.Status.do_not_disturb and before.status == discord.Status.invisible or before.status == discord.Status.offline:
#            embed = discord.Embed(
#                title="Хозяин пришёл",
#                description="Приветствуем тебя, хозяин!",
#                color=discord.Color(0xFFFFFF)
#            )
#            embed.set_image(url="https://media.tenor.com/K-wHQAtzBswAAAAd/roflan.gif")
#            await channel.send(after.mention, embed=embed)
#        elif after.status == discord.Status.offline or after.status == discord.Status.invisible:
#            embed = discord.Embed(
#                title="Хозяин ушёл",
#                description="Пока, хозяин",
#               color=discord.Color(0xFFFFFF)
#            )
#           embed.set_image(url="https://media.discordapp.net/attachments/677595846828752930/1072653866354614282/doc_2022-12-18_13-56-21_Trim_1.gif?width=747&height=560")
#            await channel.send(after.mention, embed=embed)
