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
