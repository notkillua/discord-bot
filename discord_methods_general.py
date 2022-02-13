from discord.ext import commands
import discord
from discord.ext.commands.core import has_permissions, MissingPermissions
from discord import Member


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


def setup(bot):
    bot.add_cog(General(bot))
