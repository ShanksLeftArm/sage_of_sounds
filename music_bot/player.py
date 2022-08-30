from enum import Enum
from requests import get
import discord
from discord import Message
from discord.ext import commands
import json
import asyncio
import youtube_dl

from music_bot.event_emitter import EventEmitter

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''
ydl = youtube_dl.YoutubeDL()

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls: discord.PCMVolumeTransformer, url: str, *, loop=None, stream=False) -> discord.PCMVolumeTransformer:
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(executable="C:/Program Files/ffmpeg/ffmpeg-2022-08-22-git-f23e3ce858-full_build/bin/ffmpeg.exe", source=filename, **ffmpeg_options), data=data, volume=0.20)

class AudioPlayerState(Enum):
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2
    WAITING = ( 3 )
    DEAD = 4

    def __str__(self):
        return self.name

class AudioPlayer(EventEmitter):
    def __init__(self, bot, voice_client):
        super(AudioPlayer, self).__init__()
        self.bot = bot
        self.loop = bot.loop
        self.voice_client = voice_client
        self._current_player = None
        self._source = None
        self._play_lock = asyncio.Lock()
        self.queue = []

    async def get_yt_url(self, arg):
        try:
            get(arg)
        except:
            return ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]['webpage_url']
        else:
            return arg

    async def add_to_queue(self, args):
        url = await self.get_yt_url(args)
        await self._add_url_to_queue(url)

    async def _add_url_to_queue(self, url):
        self.queue.append(url)
    
    async def clear_queue(self):
        self.queue.clear()

    def stop(self):
        self._kill_current_player()
        self.emit('stop')

    def kill(self):
        self.queue.clear()
        self._kill_current_player()

    def _kill_current_player(self):
        if self._current_player:
            try:
                self._current_player.stop()
            except OSError:
                pass
            self._current_player = None
            return True
        return False

    def pause(self):
        if self.is_playing():
            self.voice_client.pause()

    def resume(self):
        if self.is_paused() and self._current_player:
            self._current_player.resume()
            self.emit('resume')
            return
        
        if self.is_paused() and not self._current_player:
            self._kill_current_player()
            return

    
    def is_paused(self):
        return self.voice_client.is_paused()
    
    def is_playing(self):
        return self.voice_client.is_playing()

    def play(self):
        self.loop.create_task(self._play())

    async def _play(self):
        if self.is_paused() and self._current_player:
            return self.resume()

        async with self._play_lock:
            try:
                next = self.queue.pop()
            except:
                self.stop()
                return
            
            self._kill_current_player()

            self._source = await YTDLSource.from_url(next, loop=self.bot.loop, stream=True)
            self.voice_client.play(self._source, after=self._on_player_complete)
            self._current_player = self.voice_client

            self.emit('play')

    async def is_queue_empty(self):
        return len(self.queue) == 0

    async def playNext(self):
        nextUrl = self.queue.pop()
        if (nextUrl):
           await self.play(nextUrl)

    def _on_player_complete(self, error=None):
        if (error):
            return

        self.emit('song-complete', player=self)