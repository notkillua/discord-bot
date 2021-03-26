import asyncio
from time import sleep
from typing import List
from discord.ext import commands
from env import env
import discord
import sys
from db import client
db = client['discordbot_data']
# Discord bot token
TOKEN = env['DEV_TOKEN'] if sys.argv[1] == 'dev' else env['PROD_TOKEN']
# Get prefixes collection
prefixes = db['prefixes']
# Print out which type of bot is being run
if sys.argv[1] == 'dev':
    print('Development discord bot started')
else:
    print('Production discord bot running')

# Get the prefix for each message


def get_prefix(bot: commands.Bot, message: discord.Message):
    try:
        return prefixes.find_one({'id': str(message.guild.id)})['prefix']
    except:
        pass


myBot = commands.Bot(command_prefix=get_prefix)
# Extensions for discord bot
startup_extensions: List[str] = [
    'discord_methods_playlists',
    'discord_methods_general',
    'discord_methods_music'
]
# Load extensions
for extension in startup_extensions:
    myBot.load_extension(extension)


@myBot.event
async def on_guild_join(guild: discord.Guild):
    prefixes.insert_one({
        'id': str(guild.id),
        'prefix': '!'
    })
    server_count = len(myBot.guilds)
    if server_count == 1:
        await myBot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'{server_count} server'))
    else:
        await myBot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'{server_count} servers'))

# Remove prefix when removed


@myBot.event
async def on_guild_remove(guild: discord.Guild):
    prefixes.delete_one({
        'id': str(guild.id)
    })
    server_count = len(myBot.guilds)
    if server_count == 1:
        await myBot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'{server_count} server'))
    else:
        await myBot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'{server_count} servers'))

# Prefix command to change prefix


@myBot.event
async def on_ready():
    while True:
        server_count = len(myBot.guilds)
        if server_count == 1:
            await myBot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'{server_count} server'))
        else:
            await myBot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'{server_count} servers'))
        await asyncio.sleep(300)


@myBot.command(brief='Change prefix', description='Change prefix. Default prefix is !')
async def prefix(ctx, *new_prefix):
    new_prefix = ' '.join(new_prefix)
    if not new_prefix:
        return
    prefixes.update_one({
        'id': str(ctx.guild.id)
    },
        {
        '$set': {
            'prefix': new_prefix
        }
    })
    await ctx.send(f'Prefix has been changed to {new_prefix}')
# Run discord bot with token
myBot.run(TOKEN)
