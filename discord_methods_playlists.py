import emoji
from youtube_search import YoutubeSearch
from methods import getTitle
from discord.ext import commands
from db import client
import pymongo
from env import env
queue = client['discordbot_queues']

getCol = lambda name, id: client['{}_pl_{}'.format(env['DATABASE_PREFIX'], id)][name]

class Playlist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.playlist_name = None
        self.collection = None

    @commands.command(brief='Set current playlist',
                      description='Set current playlist. If playlist does not exist, it will be created when a song is added.')
    async def pset(self, ctx, *playlist_name):
        playlist_name = ' '.join(playlist_name)
        if playlist_name == '':
            return await ctx.send('Please enter a playlist name.')
        self.playlist_name = playlist_name
        self.collection: pymongo.collection = getCol(playlist_name, ctx.guild.id)
        if playlist_name in client['{}_pl_{}'.format(env['DATABASE_PREFIX'], ctx.guild.id)].list_collection_names():
            await ctx.send(f'Set current playlist to {playlist_name}.')
        else:
            await ctx.send(f'Set current playlist to {playlist_name}. The playlist will be created when a song is added.')

    @commands.command(brief='Add video to playlist',
                      description='Add video to playlist. Name of video can either be url or search term')
    async def padd(self, ctx, *name):
        if not self.playlist_name:
            return await ctx.reply('Set the playlist name with !pset <playlist name>')
        name = ' '.join(name)
        if not name:
            return await ctx.reply('Please enter a search term or url')
        if name.startswith('https://www.youtube.com'):
            url = name
        elif name.startswith('https://'):
            return await ctx.reply('Please enter a youtube url starting with https://www.youtube.com')
        else:
            results = YoutubeSearch(name, max_results=1).to_dict()[
                0]['url_suffix']
            url = f'https://youtube.com{results}'
        title = getTitle(url)
        csv_record = {
            'name': emoji.demojize(title).encode('ascii', 'ignore').decode('ascii'),
            'url': url
        }
        self.collection.insert_one(csv_record)
        await ctx.send('Added {}'.format(csv_record['url']))

    @commands.command(brief='Show songs in playlist', description='Show song in playlist')
    async def plist(self, ctx):
        if not self.playlist_name:
            return await ctx.reply('Set the playlist name with !pset <playlist name>')
        records = [record for record in self.collection.find()]
        if not records:
            return await ctx.send(f'No videos in {self.playlist_name}')
        await ctx.send(f'Showing videos from playlist {self.playlist_name}')
        for record in records:
            await ctx.send(record['url'])

    @commands.command(brief='Remove video from playlist',
                      description='Remove ONE video from playlist. Enter place of video as argument')
    async def premove(self, ctx, index):
        if not self.playlist_name:
            return await ctx.reply('Set the playlist name with !pset <playlist name>')
        result = [record for record in self.collection.find()]
        if index == 'top':
            index: int = 1
        elif index == 'bottom':
            index: int = len(result)
        else:
            try:
                index: int = int(index)
            except ValueError:
                return await ctx.reply('Index is not valid')
        index = index - 1
        try:
            record = result[index]
        except IndexError:
            return await ctx.reply('No song at that place')
        rec_id = record['_id']
        self.collection.delete_one({'_id': rec_id})
        await ctx.send(f'Removed {record["name"]}')

    @commands.command(brief='Remove all videos from playlist', description='Remove ALL videos from playlist')
    async def pclear(self, ctx):
        if not self.playlist_name:
            return await ctx.reply('Set the playlist name with !pset <playlist name>')
        await ctx.send(f'Removed {self.collection.delete_many({}).deleted_count} records')

    @commands.command(brief='Move videos in playlist',
                      description='Move videos in playlist. Same syntax as !mv command')
    async def pmove(self, ctx, begin, end):
        if not self.playlist_name:
            return await ctx.reply('Set the playlist name with !pset <playlist name>')
        res = [record for record in self.collection.find()]
        if begin == 'top':
            begin: int = 1
        elif begin == 'bottom':
            begin: int = len(res)
        else:
            try:
                begin: int = int(begin)
            except ValueError:
                return await ctx.reply('Original place for video parameter is not valid')
        if end == 'top':
            end: int = 1
        elif end == 'bottom':
            end: int = len(res)
        else:
            try:
                end: int = int(end)
            except ValueError:
                return await ctx.reply('Ending place parameter is not valid')
        begin = begin - 1
        end = end - 1
        try:
            res.insert(end, res.pop(begin))
        except IndexError:
            return await ctx.reply('No song at that place in playlist')
        self.collection.delete_many({})
        self.collection.insert_many(res)
        await ctx.send(f'Moved video from place {begin + 1} to {end + 1}')

    @commands.command(brief='Remove current playlist', description='Remove current playlist')
    async def premovep(self, ctx):
        if not self.playlist_name:
            return await ctx.reply('Set the playlist name with !pset <playlist name>')
        client['{}_pl_{}'.format(env['DATABASE_PREFIX'], ctx.guild.id)].drop_collection(self.playlist_name)
        await ctx.send(f'Removed playlist {self.playlist_name}')
        self.collection = None
        self.playlist_name = None

    @commands.command(brief='Load playlist videos into queue', description='Load playlist videos into queue')
    async def load(self, ctx):
        if not self.playlist_name:
            return await ctx.reply('Set the playlist name with !pset <playlist name>')
        result = [{ 'name': record['name'], 'url': record['url'] }
                  for record in self.collection.find()]
        client['{}_queues'.format(env['DATABASE_PREFIX'])][str(ctx.guild.id)].insert_many(result)
        await ctx.send(f'Loaded {len(result)} videos into queue')

    @commands.command(brief='Show playlists', description='Show playlists')
    async def playlists(self, ctx):
        collections = client['{}_pl_{}'.format(env['DATABASE_PREFIX'], ctx.guild.id)].list_collection_names()
        if collections:
            await ctx.send('Playlists:')
        else:
            await ctx.send('No playlists')
        [await ctx.send(collection) for collection in collections]

    @commands.command(brief='Rename playlist', description='Rename playlist')
    async def prename(self, ctx, *new_name):
        new_name = ' '.join(new_name)
        if not self.playlist_name:
            return await ctx.reply('Set the playlist name with !pset <playlist name>')
        if new_name == self.playlist_name:
            return await ctx.reply('You are not changing the name of the playlist')
        if new_name in client['{}_pl_{}'.format(env['DATABASE_PREFIX'], ctx.guild.id)].list_collection_names():
            return await ctx.reply('Name is already taken')
        self.collection.rename(new_name)
        await ctx.send(f'Renamed playlist {self.playlist_name} to {new_name}')
        self.playlist_name = new_name

    @commands.command(brief='Save current queue to the playlist', description='Saves current queue to the playlist')
    async def save(self, ctx):
        if not self.playlist_name:
            return await ctx.reply('Set the playlist name with !pset <playlist name>')
        collection = queue[str(ctx.message.guild.id)]
        songs = [{ 'name': i['name'], 'url': i['url'] } for i in collection.find()]
        self.collection.insert_many(songs)
        await ctx.send(f'Saved song to to playlist {self.playlist_name}')

    @commands.command(brief='Get the current playlist', description='Gets the current playlist')
    async def playlist(self, ctx):
        if self.playlist_name:
            await ctx.send(f'Current playlist is {self.playlist_name}')
        else:
            await ctx.send('No playlist set')


def setup(bot: commands.Bot):
    bot.add_cog(Playlist(bot))
