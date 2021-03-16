import csv
import emoji
from youtube_search import YoutubeSearch
from methods import getTitle
from discord.ext import commands
from db import client
import pymongo
db = client['discordbot_playlists']
playlist_data_db = client['discordbot_data']['playlist_data']


def checkName(name: str):
    playlists = db.list_collection_names()
    if name in playlists:
        return False
    return True


async def checkUser(ctx, name, message):
    if not playlist_data_db.find_one({'name': name})['author_id'] == str(ctx.author.id):
        await ctx.reply(message)
        return True


class Playlist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.playlist_name = None
        self.collection = None

    @commands.command(brief='Set current playlist',
                      description='Set current playlist so that you don\'t have to keep saying playlist name in playlist commands')
    async def pset(self, ctx, *playlist_name):
        playlist_name = ' '.join(playlist_name)
        if checkName(playlist_name):
            return await ctx.reply('No playlist with that name')
        playlist = playlist_data_db.find_one({'name': playlist_name})
        if (not playlist['server_id'] == str(ctx.guild.id)) and playlist['private']:
            return await ctx.reply('No playlist with that name')
        self.playlist_name = playlist_name
        self.collection: pymongo.collection = db[playlist_name]
        await ctx.send(f'Changed playlist to {playlist_name}')

    @commands.command(brief='Create playlist',
                      description='Create playlist. Playlist can have spaces and Uppercase lettersbut cannot be called playlist_data')
    async def pcreate(self, ctx, private, *playlist_name):
        try:
            private: bool = bool(int(private))
        except ValueError:
            return await ctx.reply('Private value can only be 0 (public) or 1 (private)')
        playlist_name = ' '.join(playlist_name)
        if not checkName(playlist_name):
            return await ctx.reply('Already have playlist with same name')
        if not playlist_name:
            return await ctx.reply('Playlist name cannot be empty')
        db.create_collection(playlist_name)
        playlist_data_db.insert_one({
            'name': playlist_name,
            'private': private,
            'author_id': str(ctx.author.id),
            'server_id': str(ctx.guild.id)
        })
        self.playlist_name = playlist_name
        self.collection: pymongo.collection = db[playlist_name]
        if private:
            await ctx.send(f'Created private playlist {playlist_name}')
        else:
            await ctx.send(f'Created public playlist {playlist_name}')

    @commands.command(brief='Add video to playlist',
                      description='Add video to playlist. Name of video can either be url or search term')
    async def padd(self, ctx, *name):
        if not self.playlist_name:
            return await ctx.reply('Set the playlist name with !pset <playlist name>')
        if checkName(self.playlist_name):
            return await ctx.reply('No playlist with that name')
        if await checkUser(ctx, self.playlist_name, 'You are not the owner of the playlist, you cannot add to it'):
            return
        name = ' '.join(name)
        if not name:
            return await ctx.reply('Please enter a search term or url')
        if name.startswith('https://www.youtube.com'):
            url = name
        elif name.startswith('https://'):
            return await ctx.reply('Please enter a youtube url')
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

    @commands.command(brief='Show queue of playlist', description='Show queue of playlist in order of playing order')
    async def pqueue(self, ctx):
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
        if await checkUser(ctx, self.playlist_name, 'You are not the owner, so you cannot remove from it'):
            return
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
    async def premoveall(self, ctx):
        if not self.playlist_name:
            return await ctx.reply('Set the playlist name with !pset <playlist name>')
        if await checkUser(ctx, self.playlist_name, 'You are not the owner, so you cannot remove from it'):
            return
        count = len([record for record in self.collection.find()])
        self.collection.delete_many({})
        await ctx.send(f'Removed {count} records')

    @commands.command(brief='Move videos in playlist',
                      description='Move videos in playlist. Same syntax as !mv command')
    async def pmove(self, ctx, begin, end):
        if not self.playlist_name:
            return await ctx.reply('Set the playlist name with !pset <playlist name>')
        if await checkUser(ctx, self.playlist_name, 'You are not the owner, so you cannot move around videos'):
            return
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

    @commands.command(brief='Remove playlist', description='Remove WHOLE playlist. Enter playlist name')
    async def premovep(self, ctx, *name):
        name = ' '.join(name)
        if not name:
            return await ctx.reply('Playlist name cannot be empty')
        if checkName(name):
            return await ctx.reply(f'{name} is not a playlist')
        if await checkUser(ctx, name, 'You are not the owner of the playlist, so you cannot delete the playlist'):
            return
        db[name].drop()
        playlist_data_db.delete_one({'name': name})
        if name == self.playlist_name:
            self.collection = None
            self.playlist_name = None
        await ctx.send(f'Removed playlist {name}')

    @commands.command(brief='Load playlist videos into queue', description='Load playlist videos into queue')
    async def load(self, ctx):
        if not self.playlist_name:
            return await ctx.reply('Set the playlist name with !pset <playlist name>')
        result = [[record['name'], record['url']]
                  for record in self.collection.find()]
        print(result)
        with open(f'{ctx.message.guild.id}.csv', 'a+', newline='\n') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(result)
            await ctx.send(f'Loaded {len(result)} songs.')

    @commands.command(brief='Show playlists', description='Show playlists')
    async def playlists(self, ctx):
        collections = [collection for collection in playlist_data_db.find() if(collection['private'] is False or (
            collection['private'] is True and collection['server_id'] == str(ctx.guild.id)))]
        if collections:
            await ctx.send('Playlists:')
        else:
            await ctx.send('No playlists')
        [await ctx.send('{name} - {public}'.format(name=collection['name'], public='private' if collection['private'] else 'public')) for collection in collections]

    @commands.command(brief='Rename playlist', description='Rename playlist')
    async def prename(self, ctx, *new_name):
        new_name = ' '.join(new_name)
        if not self.playlist_name:
            return await ctx.reply('Set the playlist name with !pset <playlist name>')
        if await checkUser(ctx, self.playlist_name, 'You are not the owner of the playlist, so you cannot rename it'):
            return
        if new_name == self.playlist_name:
            return await ctx.reply('You are not changing the name of the playlist')
        if new_name in db.list_collection_names():
            return await ctx.reply('Name is already taken by another playlist, or there is another private playlist in another server. Use !playlists to which ones are taken')
        if new_name == 'playlist_data':
            return await ctx.reply('Name is forbidden. Please choose a different one.')
        self.collection.rename(new_name)
        playlist_data_db.update_one({'name': self.playlist_name}, {
            '$set': {'name': new_name}})
        await ctx.send(f'Renamed playlist {self.playlist_name} to {new_name}')
        self.playlist_name = new_name

    @commands.command(brief='Save current queue to the playlist', description='Saves current queue to the playlist')
    async def save(self, ctx):
        if not self.playlist_name:
            return await ctx.reply('Set the playlist name with !pset <playlist name>')
        if await checkUser(ctx, self.playlist_name, 'You are not the owner of the playlist, so you cannot save songs to it'):
            return
        with open(f'{ctx.message.guild.id}.csv') as csvfile:
            reader = csv.reader(csvfile)
            songs = [{
                'name': song[0],
                'url': song[1]
            } for song in reader]
            self.collection.delete_many({})
            self.collection.insert_many(songs)
            await ctx.send(f'Saved data to playlist {self.playlist_name}')

    @commands.command(brief='Get the current playlist', description='Gets the current playlist')
    async def playlist(self, ctx):
        if self.playlist_name:
            await ctx.send(f'Current playlist is {self.playlist_name}')
        else:
            await ctx.send('No playlist set')


def setup(bot: commands.Bot):
    bot.add_cog(Playlist(bot))
