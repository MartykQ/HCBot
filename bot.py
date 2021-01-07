import aiohttp
import discord
import asyncio

from discord.ext import commands
from utils import block_maping, help_str
import os
from dotenv import load_dotenv

load_dotenv()

bot = commands.Bot(command_prefix='>')

async def api_call(path):
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{path}') as r:
            if r.status == 200:
                js = await r.json()
                return js

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()


async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[fetch(session, url) for url in urls], return_exceptions=True)
        return results

def get_event_value(name, value):
    if name == 'rank':
        return value + 1000
    elif name == 'time':
        return value / 3600
    else:
        return value


@bot.command(name='topka', help='Topka gildyjna')
async def nine_nine(ctx, guild, event_name):

    try:
        event_type = block_maping[event_name]
    except KeyError:
        await ctx.send(help_str)
        return

    guild_data = await api_call(f"https://kwadratowa.games/api/guild/{guild.upper()}")
    if not guild_data:
        await ctx.send("Nie ma takiej gildii!")
        return

    members = guild_data["members"]
    urls = []
    for id, nickname in members.items():
        urls.append(f"https://kwadratowa.games/api/profile/{id}")

    responses = await fetch_all(urls)

    rank_data = []
    for obj in responses:
        rank_data.append({
            'name': obj['hardcore']['data']['!nickname'],
            'value': get_event_value(event_name, float(obj['hardcore']['data'].get(event_type, 0.0)))
             })

    rank_data = sorted(rank_data, key=lambda k: k['value'], reverse=True)
    return_string = f"```\nRanking {event_type}:\n"

    for idx, record in enumerate(rank_data):
        return_string += f"\n{idx+1}: {record['name']} | {record['value']}"

    return_string += '```'

    await ctx.send(f"{return_string[:1999]}")


@bot.command(name='top50', help='Topka globalna.')
async def top50(ctx, event_name):

    try:
        event_type = block_maping[event_name]
    except KeyError:
        await ctx.send(help_str)
        return

    guild_data = await api_call("https://kwadratowa.games/api/guild")
    guild_urls = []
    for guild in guild_data:
        guild_urls.append(f"https://kwadratowa.games/api/guild/{guild['code']}")

    all_guilds_fetched = await fetch_all(guild_urls)

    urls = []
    for guild in all_guilds_fetched:
        members = guild['members']
        for id, nickname in members.items():
            urls.append(f"https://kwadratowa.games/api/profile/{id}")

    responses = await fetch_all(urls)
    rank_data = []
    for obj in responses:
        rank_data.append({
            'guild': obj['hardcore']['guild'],
            'name': obj['hardcore']['data']['!nickname'],
            'value':get_event_value(event_name, float(obj['hardcore']['data'].get(event_type, 0)))})

    rank_data = sorted(rank_data, key=lambda k: k['value'], reverse=True)

    return_string = f"\n**Ranking {event_type}:**\n```"
    for idx, record in enumerate(rank_data[:50]):
        return_string += f"\n{idx+1}: {record['guild']} {record['name']} | {record['value']}"

    return_string += '```'

    await ctx.send(f"{return_string[:1999]}")

bot.run('123')

