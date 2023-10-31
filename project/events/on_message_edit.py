import discord
import datetime

from project import bot, contracts, Base, Session, config, admin_roles, dev_channels, engine
from project.models import Contracts, Coffers, DailyTasks, Users

from sqlalchemy import cast, Date, or_, and_


@bot.event
async def on_message_edit(before, after):
    if not after.author == bot.user:
        if not before.channel.id in dev_channels:
            with Session() as session:
                user = session.query(Users).filter_by(discord_user=after.author.id).first()

            try:
                dev_messages = after.guild.get_channel(config["guild"]["logs"]["messages"])
            except:
                return

            on_message_edit_embed = discord.Embed(
                title="Message Edited",
                color=0xFFFFFF,
                timestamp=datetime.datetime.now()
            )
            on_message_edit_embed.add_field(name="User", value=after.author, inline=False)
            on_message_edit_embed.add_field(name="User mention", value=after.author.mention, inline=False)
            on_message_edit_embed.add_field(name="User ID", value=after.author.id, inline=False)

            if not user is None:
                on_message_edit_embed.add_field(name="Nickname", value=user.nickname, inline=False)

            on_message_edit_embed.add_field(name="Channel", value=after.channel.mention, inline=False)
            on_message_edit_embed.add_field(name="Channel ID", value=after.channel.id, inline=False)
            on_message_edit_embed.add_field(name="Message content (Old)", value=before.content, inline=False)
            on_message_edit_embed.add_field(name="Message content (New)", value=after.content, inline=False)
            on_message_edit_embed.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

            await dev_messages.send(embed=on_message_edit_embed)
