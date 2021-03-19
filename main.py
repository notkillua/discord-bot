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
# All the parts of the embed
description = '''
Musical is a music bot that can play music in voice channels.
Musical is very similar to another discord bot called Rhythm.
Both bots have the same purpose of playing music, and have queues and playlists.
'''
important_commands = '''
The default command prefix is !, but you can change it with !prefix <new prefix>.
Some important commands are !queue (to show queue), !add <search term or youtube url> (add song to queue),
!remove <index of song> (remove song from queue), and !mv <begin> <end> (move songs around in queue).
For all the commands, run the command !help
'''
contributions = '''
Any contributions are highly appreciated as this was made by one person.
Any reported bugs or issues are also highly appreciated as this is a relatively new bot.
Github link: https://github.com/cubix11/discord-bot-musical
'''
embed = discord.Embed(title='Musical Discord Bot', description=description)
embed.add_field(name='Import Commands', value=important_commands, inline=False)
embed.add_field(name='Contributions', value=contributions, inline=False)
# Print out which type of bot is being run
if sys.argv[1] == 'dev':
    print('Development discord bot started')
else:
    print('Production discord bot running')

# Get the prefix for each message


def get_prefix(bot: commands.Bot, message: discord.Message):
    return prefixes.find_one({'id': str(message.guild.id)})['prefix']


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

# Add prefix to collection on join


@myBot.event
async def on_guild_join(guild: discord.Guild):
    prefixes.insert_one({
        'id': str(guild.id),
        'prefix': '!'
    })
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me):
            await channel.send(embed=embed)
            break

# Remove prefix when removed


@myBot.event
async def on_guild_remove(guild: discord.Guild):
    prefixes.delete_one({
        'id': str(guild.id)
    })

# Prefix command to change prefix


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
