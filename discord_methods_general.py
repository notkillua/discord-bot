from discord.ext import commands
from db import client
from env import env
db = client[env['DATABASE_PREFIX']]
prefixes = db['prefixes']

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='hello', brief='Says hello', description='Says hello')
    async def hello(self, ctx) -> None:
        await ctx.reply(f'Hello there, {str(ctx.author)}')

    @commands.command(brief='Changes nickname of Bot', description='Syntax: !nick <new name>')
    async def nick(self, ctx, *nick) -> None:
        nick = ' '.join(nick)
        await ctx.me.edit(nick=nick)
        await ctx.reply(f'Nickname changed to {nick}')

    @commands.command(brief='Change prefix', description='Change prefix. Default prefix is !')
    async def prefix(self, ctx, *new_prefix):
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


def setup(bot):
    bot.add_cog(General(bot))
