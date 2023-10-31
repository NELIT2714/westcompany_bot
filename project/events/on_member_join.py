import discord
import datetime

from project import bot, contracts, Base, Session, config, admin_roles, engine
from project.models import Contracts, Coffers, DailyTasks, Users
from discord.utils import format_dt

from sqlalchemy import cast, Date, or_, and_


@bot.event
async def on_member_join(member):
    guest_role = discord.utils.get(member.guild.roles, id=config["guild"]["ids-list"]["roles"]["guest"])
    channel = member.guild.get_channel(config["guild"]["ids-list"]["channels"]["greetings"])
    dev_users = member.guild.get_channel(config["guild"]["logs"]["users"])

    embed_after_join = discord.Embed(
        title="Новый участник",
        description=f"Приветствуем нового пользователя {member.mention} на Discord сервере сообщества WestCompany.\
                    \Мы рады каждому, кто присоединился к нам. Узнать подробнее о сообществе можно в канале <#1107937278363455518>",
        color=discord.Color(0xFFFFFF)
    )
    embed_after_join.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)
    embed_after_join.set_thumbnail(url=bot.user.avatar.url)

    on_member_join_embed = discord.Embed(
        title="Member Join",
        color=0xFFFFFF,
        timestamp=datetime.datetime.now()
    )
    on_member_join_embed.add_field(name="User", value=member, inline=False)
    on_member_join_embed.add_field(name="User mention", value=member.mention, inline=False)
    on_member_join_embed.add_field(name="User ID", value=member.id, inline=False)
    on_member_join_embed.add_field(name="Reg date", value=format_dt(member.created_at, "D"), inline=False)
    on_member_join_embed.add_field(name="Join date", value=format_dt(member.joined_at, "D"), inline=False)

    on_member_join_embed.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

    await member.add_roles(guest_role)
    await channel.send(f"{member.mention}", embed=embed_after_join)
    await dev_users.send(embed=on_member_join_embed)

    with Session() as session:
        user = session.query(Users).filter_by(discord_user=member.id).first()

    if not user is None:
        member_role = discord.utils.get(member.guild.roles, id=config["guild"]["ids-list"]["roles"]["member"])

        await member.add_roles(member_role)
        await member.edit(nick=user.nickname)
