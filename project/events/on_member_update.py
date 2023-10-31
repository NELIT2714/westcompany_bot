import discord
import datetime

from project import bot, contracts, Base, Session, config, admin_roles, engine
from project.models import Contracts, Coffers, DailyTasks, Users

from sqlalchemy import cast, Date, or_, and_


@bot.event
async def on_member_update(before, after):
    if not after == bot.user:
        guest_role = discord.utils.get(after.guild.roles, id=config["guild"]["ids-list"]["roles"]["guest"])
        member_role = discord.utils.get(after.guild.roles, id=config["guild"]["ids-list"]["roles"]["member"])
        highrank = discord.utils.get(after.guild.roles, id=config["guild"]["ids-list"]["roles"]["highrank"])

        with Session() as session:
            user = session.query(Users).filter_by(discord_user=after.id).first()

        if user is None:
            for role in after.roles:
                await after.remove_roles(role)
        else:
            await after.add_roles(member_role)

        if not after.display_name == user.nickname:
            try:
                await after.edit(nick=user.nickname)
            except Exception as error:
                print(error)

        if len(after.roles) == 1 and not guest_role in after.roles:
            await after.add_roles(guest_role)
        elif len(after.roles) > 2 and guest_role in after.roles:
            await after.remove_roles(guest_role)

        if highrank in after.roles and highrank not in before.roles:
            if not any(admin_role.id in admin_roles for admin_role in after.roles):
                await after.remove_roles(highrank)

        if any(admin_role.id in admin_roles for admin_role in after.roles):
            await after.add_roles(highrank)
        else:
            await after.remove_roles(highrank)