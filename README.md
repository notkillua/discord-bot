# Musical
## Description
Musical is a discord bot that will play music in voice channels.  
Musical has many commands for adding, moving, deleting for queues and playlists.
## Contributions
Any contributions are highly appreciated as this was made by one person and it is a relatively new bot.
## Technology
Database: mongodb
Discord library: discord.py
Queues: stored in csv files dynamically created
## Instructions To Run
Because in the env file there is are separate tokens for production and development, you need to run the python file (development) as
```bash
python main.py dev
```
and python file (production) as
```
python main.py prod
```
## Commands
### General
ban - Bans member  
hello - Says hello  
kick - Kicks member  
nick - Changes nickname of Bot  
unban - Unbans member
### Music
add - Adds song to queue  
joinJoins video channel  
leave - Leaves voice channel  
loop - Loop queue  
lyrics - Show lyrics of song  
mute - Mute someone  
mv - Move video in queue  
place - Go to specific song in the queue  
play - Plays song  
queue - Show queue  
remove - Removes song  
removeall - Removes all songs in queue  
skip - Skip current song  
status - Show status of video  
stop - Stops video  
toggle - Toggles state of video  
vide - oGives current song
### Playlist
load - Load playlist videos into queue  
padd - Add video to playlist  
pcreate - Create playlist  
playlist - Get the current playlist  
playlists - Show playlists  
pmove - Move videos in playlist  
pqueue - Show queue of playlist  
premove - Remove video from playlist  
premoveall - Remove all videos from playlist  
premovep - Remove playlist  
prename - Rename playlist  
pset - Set current playlist  
save - Save current queue to the playlist
### No Category
help - Shows all commands  
prefix - Change prefix