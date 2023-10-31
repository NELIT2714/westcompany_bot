import discord
import datetime

from project import bot, contracts, Base, Session, config, admin_roles, engine
from project.models import Contracts, Coffers, DailyTasks, Users
from discord.utils import format_dt

from sqlalchemy import cast, Date, or_, and_


@bot.event
async def on_member_remove(member):
    dev_users = member.guild.get_channel(config["guild"]["logs"]["users"])

    on_member_remove_embed = discord.Embed(
        title="Member Left",
        color=0xFFFFFF,
        timestamp=datetime.datetime.now()
    )
    on_member_remove_embed.add_field(name="User", value=member, inline=False)
    on_member_remove_embed.add_field(name="User mention", value=member.mention, inline=False)
    on_member_remove_embed.add_field(name="User ID", value=member.id, inline=False)
    on_member_remove_embed.add_field(name="Reg date", value=format_dt(member.created_at, "D"), inline=False)
    on_member_remove_embed.add_field(name="Join date", value=format_dt(member.joined_at, "D"), inline=False)
    on_member_remove_embed.add_field(name="Left date", value=format_dt(datetime.datetime.now(), "D"), inline=False)

    on_member_remove_embed.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

    await dev_users.send(embed=on_member_remove_embed)

    with Session() as session:
        user = session.query(Users).filter_by(discord_user=member.id).first()
