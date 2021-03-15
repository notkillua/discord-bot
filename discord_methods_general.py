from discord.ext import commands
import discord
from discord.ext.commands.core import has_permissions, MissingPermissions


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='hello', brief='Says hello', description='Says hello')
    async def hello(self, ctx) -> None:
        await ctx.reply(f'Hello there, {str(ctx.author)}')

    @commands.command(brief='Changes nickname of Bot', description='Syntax: !nick <new name>')
    @has_permissions(kick_members=True, ban_members=True)
    async def nick(self, ctx, *nick) -> None:
        nick = ' '.join(nick)
        await ctx.me.edit(nick=nick)

    @commands.command(brief='Bans member', description='Syntax: !ban @<member name> <reason>')
    @has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.User,*reason) -> None:
        reason = ' '.join(reason)
        await ctx.guild.ban(member, reason=reason)
        await ctx.reply('User has been banned')

    @commands.command(brief='Unbans member', description='Syntax: !unban @<member name> <reason>')
    @has_permissions(ban_members=True)
    async def unban(self, ctx, member: discord.User) -> None:
        await ctx.guild.unban(member)
        await ctx.reply('User has been unbanned')

    @commands.command(brief='Kicks member', description='Syntax: !kick @<member name>')
    @has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member) -> None:
        await member.kick()
        await ctx.reply('User has been kicked')

    @ban.error
    @kick.error
    @unban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            await ctx.send('You don\'t have the correct permissions')


def setup(bot):
    bot.add_cog(General(bot))
