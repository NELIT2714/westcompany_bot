import discord
import datetime

from project import bot, contracts, Base, Session, config, admin_roles, dev_channels, engine
from project.models import Contracts, Coffers, DailyTasks, Users

from sqlalchemy import cast, Date, or_, and_


@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if not message.author == bot.user:
        if not message.channel.id in dev_channels:
            with Session() as session:
                user = session.query(Users).filter_by(discord_user=message.author.id).first()

            try:
                dev_messages = message.guild.get_channel(config["guild"]["logs"]["messages"])
            except:
                return

            on_message_embed = discord.Embed(
                title="New Message",
                color=0xFFFFFF,
                timestamp=datetime.datetime.now()
            )
            on_message_embed.add_field(name="User", value=message.author, inline=False)
            on_message_embed.add_field(name="User mention", value=message.author.mention, inline=False)
            on_message_embed.add_field(name="User ID", value=message.author.id, inline=False)

            if not user is None:
                on_message_embed.add_field(name="Nickname", value=user.nickname, inline=False)

            on_message_embed.add_field(name="Channel", value=message.channel.mention, inline=False)
            on_message_embed.add_field(name="Channel ID", value=message.channel.id, inline=False)
            on_message_embed.add_field(name="Message content", value=message.content, inline=False)
            on_message_embed.set_footer(text="WestCompany Bot", icon_url=bot.user.avatar.url)

            await dev_messages.send(embed=on_message_embed)
