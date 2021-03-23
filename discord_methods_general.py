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
    @has_permissions(kick_members=True, ban_members=True)
    async def nick(self, ctx, *nick) -> None:
        nick = ' '.join(nick)
        await ctx.me.edit(nick=nick)

    @commands.command(brief='Mute someone', description='Mute will mute a member. Just pass in the member with an @ sign and 1 or 0 for muted or not')
    @has_permissions(ban_members=True)
    async def mute(self, ctx, member: Member, value: bool):
        try:
            await member.edit(mute=value)
        except discord.errors.HTTPException:
            return await ctx.reply('User must be connected to a voice channel')
        await ctx.send('{member} has been {status}'.format(member=member.display_name, status='muted' if value else 'unmuted'))

    @mute.error
    async def permissions_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            await ctx.send('You don\'t have the correct permissions')


def setup(bot):
    bot.add_cog(General(bot))
