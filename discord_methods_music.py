from discord.ext.commands import MissingPermissions, has_permissions
from methods import getTitle, create
from discord.ext import commands
from youtube_search import YoutubeSearch
from youtube_dl import YoutubeDL
import csv
import emoji
from discord import utils, Member
import discord
import asyncio
from youtube_title_parse import get_artist_title
from lyricsgenius import Genius
from env import env

api = Genius(env['GENIUS_ACCESS_TOKEN'])


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.add = None
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 1',
            'options': '-vn'
        }
        self.stopped = False
        self.skip_song = False
        self.loop = {}
        self.ydl_options = {'format': 'bestaudio', 'noplaylist': 'True'}
        self.song = None
        self.place = 0
        self.go = None
        self.queue = None

    @commands.command(brief='Adds song to queue', description='Adds song to queue')
    async def add(self, ctx, *name):
        name = ' '.join(name)
        if name.startswith('https://youtube.com'):
            url = name
        else:
            try:
                results = YoutubeSearch(name, max_results=1).to_dict()
                if not results:
                    return await ctx.reply('No videos found. Please enter a more clearer search term')
                results = results[0]['url_suffix']
            except KeyError:
                return await ctx.reply('Sorry, but something has gone wrong when searching youtube. Please try the command again')
            url = f'https://youtube.com{results}'
        with open(f'{ctx.message.guild.id}.csv', 'a+', newline='\n') as csvfile:
            writer = csv.writer(csvfile)
            title = getTitle(url)
            csv_record = (emoji.demojize(title).encode(
                'ascii', 'ignore').decode('ascii'), url)
            self.add = csv_record
            writer.writerow(csv_record)
            await ctx.send(f'Added {url}')

    @commands.command(brief='Plays song', description='Will play all songs in the queue')
    async def play(self, ctx):
        create(ctx.message.guild.id)
        with open(f'{ctx.message.guild.id}.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            voice = utils.get(self.bot.voice_clients, guild=ctx.guild)
            if not voice:
                return await ctx.reply('Not in voice channel')
            self.queue = [video for video in reader]
            self.add = None
            while True:
                for song in range(len(self.queue)):
                    i = self.queue[song]
                    self.place += 1
                    with YoutubeDL(self.ydl_options) as ydl:
                        info = ydl.extract_info(i[1], download=False)
                    yt_url = info['formats'][0]['url']
                    if self.go == self.place or not self.go:
                        await ctx.send(f'Now playing: {emoji.emojize(i[0])}')
                    self.song = [i[0], song]
                    voice.play(discord.FFmpegPCMAudio(
                        yt_url, **self.FFMPEG_OPTIONS))
                    while True:
                        if not voice.is_playing() and not voice.is_paused() and not self.skip_song and self.stopped:
                            self.stopped = False
                            self.song = None
                            self.place = 0
                            return
                        if not voice.is_playing() and not voice.is_paused() and not self.skip_song and not self.stopped:
                            break
                        if (self.skip_song and not self.stopped) or (self.go and self.go > self.place):
                            self.skip_song = False
                            voice.stop()
                            break
                        elif self.go == self.place:
                            self.go = None
                        if voice.is_playing() or voice.is_paused():
                            if self.add:
                                self.queue.append(self.add)
                                self.add = None
                            await asyncio.sleep(0.1)
                self.song = None
                self.place = None
                if self.loop.get(ctx.guild.id, False):
                    await ctx.send('Looping...')
                    self.place = 0
                else:
                    await ctx.send('No more songs in queue')
                    await ctx.send('Done')
                    self.place = None
                    self.queue = None
                    break

    @ commands.command(brief='Go to specific song in the queue', description='Go to specific song in the queue')
    async def place(self, ctx, place):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not voice:
            return await ctx.reply('Not in voice channel')
        if not voice.is_playing():
            return await ctx.reply('Not playing song')
        try:
            place = int(place)
            queue_length = len(self.queue)
            if place > queue_length:
                return await ctx.reply('Place value is over the length of the queue')
            elif place <= self.place:
                return await ctx.reply('The place value you want to go to is has already passed or is the current song.')
            self.go = place
            await ctx.send(f'Moving to place {place}')
        except ValueError:
            await ctx.reply('Place value must be a number')

    @ commands.command(brief='Show queue', description='Show queue')
    async def queue(self, ctx):
        create(ctx.message.guild.id)
        with open(f'{ctx.message.guild.id}.csv', 'r+') as csvfile:
            reader = csv.reader(csvfile)
            rows = [row for row in reader]
            if not rows:
                await ctx.send('No songs in queue')
            for row in rows:
                await ctx.send(row[1])

    @ commands.command(brief='Move video in queue', description='!mv (beginning place of video) (end place of video)')
    async def mv(self, ctx, beginning: str, end: str):
        create(ctx.message.guild.id)
        with open(f'{ctx.message.guild.id}.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            rows = [row for row in reader]
        if beginning == 'top':
            beginning: int = 1
        elif beginning == 'bottom':
            beginning: int = len(rows)
        else:
            try:
                beginning: int = int(beginning)
            except ValueError:
                return await ctx.reply('Original place for video parameter is not valid')
        if end == 'top':
            end: int = 1
        elif end == 'bottom':
            end: int = len(rows)
        else:
            try:
                end: int = int(end)
            except ValueError:
                return await ctx.reply('Ending place parameter is not valid')
        beginning = beginning - 1
        end = end - 1
        try:
            rows.insert(end, rows.pop(beginning))
        except IndexError:
            return await ctx.reply('No song at that spot in the queue.')
        with open(f'{ctx.message.guild.id}.csv', 'w', newline='\n') as csvfile:
            csvfile.truncate()
            writer = csv.writer(csvfile)
            writer.writerows(rows)
            await ctx.reply(f'Moved song from place {beginning + 1} to place {end + 1}')

    @ commands.command(brief='Skip current song', description='Skips current song')
    async def skip(self, ctx):
        self.skip_song = True
        self.stopped = False

    @ commands.command(brief='Stops video', description='Stops video')
    async def stop(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not voice.is_playing():
            return await ctx.reply('Not playing song')
        self.skip_song = False
        self.stopped = True
        voice.stop()
        await ctx.send('Stopped')

    @ commands.command(brief='Removes song', description='Removes the index of the song in queue')
    async def remove(self, ctx, index: str):
        with open(f'{ctx.message.guild.id}.csv', 'r', newline='\n') as csvfile:
            reader = csv.reader(csvfile)
            rows = [row for row in reader]
        if index == 'top':
            index: int = 1
        elif index == 'bottom':
            index: int = len(rows)
        else:
            try:
                index: int = int(index)
            except ValueError:
                return await ctx.reply('Index is not valid')
        index = index - 1
        create(ctx.message.guild.id)
        try:
            del rows[index]
        except IndexError:
            return await ctx.reply('No song at that spot in the queue.')
        with open(f'{ctx.message.guild.id}.csv', 'w', newline='\n') as csvfile:
            csvfile.truncate()
            writer = csv.writer(csvfile)
            writer.writerows(rows)
        await ctx.send('Deleted')

    @ commands.command(brief='Toggles state of video', description='Pauses or plays video depending on the state of it')
    async def toggle(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not voice:
            return await ctx.reply('Not in voice channel')
        if voice.is_playing():
            voice.pause()
            await ctx.send('Now paused')
        else:
            voice.resume()
            await ctx.send('Now playing')

    @ commands.command(brief='Removes all songs in queue', description='Removes all songs in queue')
    async def removeall(self, ctx) -> None:
        file = open(f'{ctx.message.guild.id}.csv', 'w+')
        file.truncate()
        file.close()
        await ctx.send('Removed all')

    @ commands.command(brief='Show status of video', description='Shows whether the video is playing or is paused')
    async def status(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not voice:
            return await ctx.reply('Not in voice channel right now')
        if voice.is_playing():
            await ctx.send('Status: playing video')
        elif voice.is_paused():
            await ctx.send('Status: video paused')
        else:
            await ctx.send('Status: video not on or stopped')

    @ commands.command(brief='Loop queue', description='Loop the queue with !loop (1 or 0 for true or false)')
    async def loop(self, ctx, loop_true=None):
        if loop_true:
            self.loop[ctx.guild.id] = bool(int(loop_true))
            await ctx.reply(f'Looping set to {self.loop[ctx.guild.id]}')
        else:
            await ctx.reply(f'Currently looping is set to {self.loop.get(ctx.guild.id, False)}')

    @ commands.command(brief='Gives current song', description='Gives current song')
    async def video(self, ctx):
        if not self.song:
            await ctx.reply('Bot is not playing song')
        else:
            await ctx.send(f'Current song: {self.song[0]}')

    @ commands.command(brief='Show lyrics of song', description='Show lyrics of song')
    async def lyrics(self, ctx, *author_song):
        author_song = ' '.join(author_song)
        if not self.song:
            return await ctx.reply('No song playing right now.')
        if not author_song:
            video = get_artist_title(self.song[0])
            if not video:
                return await ctx.reply('Video is not a song')
            else:
                artist, title = video
        else:
            artist, title = author_song.split(" | ")
        song_lyrics = api.search_song(f'{artist} {title}')
        if song_lyrics:
            for line in song_lyrics.lyrics.split('\n'):
                if line:
                    await ctx.send(line)
        else:
            await ctx.reply('Lyrics could not be found.')

    @ commands.command(brief='Joins video channel', description='Pass in voice channel and it will go into it')
    async def join(self, ctx, *name) -> None:
        name = ' '.join(name)
        vc = utils.get(ctx.guild.voice_channels, name=name)
        if vc:
            voice = utils.get(self.bot.voice_clients, guild=ctx.guild)
            if voice:
                await ctx.send('Already connected to another channel')
            else:
                await vc.connect()
                await ctx.send(f'Successfully connected to {name}')
        else:
            await ctx.reply('No voice channel with that name')

    @ commands.command(brief='Leaves voice channel', description='Leaves voice channel')
    async def leave(self, ctx):
        if ctx.voice_client:
            self.stopped = True
            self.skip_song = False
            await ctx.voice_client.disconnect()
            await ctx.send('Successfully disconnected!')
        else:
            await ctx.reply('Bot is not in voice channel')

    @ commands.command(brief='Mute someone', description='Mute someone')
    @ has_permissions(kick_members=True, ban_members=True)
    async def mute(self, ctx, member: Member, value: bool):
        value = ('muted', True) if value else ('unmuted', False)
        await member.edit(mute=value[1])
        await ctx.send(f'{member.display_name} has been {value[0]}')

    @ mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            await ctx.send("You don't have the correct permissions")


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))