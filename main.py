import asyncio
from typing import List
from discord.ext import commands
from env import env
import discord
import sys
from db import client
db = client[env['DATABASE_PREFIX']]
# Discord bot token
TOKEN = env['DEV_TOKEN'] if sys.argv[1] == 'dev' else env['PROD_TOKEN']
# Get prefixes collection
prefixes = db['prefixes']
# Print out which type of bot is being run
if sys.argv[1].lower() == 'dev':
    print('Development discord bot started')
else:
    print('Production discord bot running')

# Get the prefix for each message

def get_prefix(bot: commands.Bot, message: discord.Message):
    prefix = prefixes.find_one({'id': str(message.guild.id)})
    if prefix:
        return prefix['prefix']
    else:
        prefixes.insert_one({
            'id': str(message.guild.id),
            'prefix': '!'
        })
        return '!'

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


@myBot.event
async def on_ready():
    while True:
        server_count = len(myBot.guilds)
        if server_count == 1:
            await myBot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'{server_count} server'))
        else:
            await myBot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'{server_count} servers'))
        await asyncio.sleep(300)
# Run discord bot with token
myBot.run(TOKEN)
