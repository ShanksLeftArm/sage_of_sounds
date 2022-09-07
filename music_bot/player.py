from enum import Enum
from random import shuffle
from requests import get
from discord import VoiceProtocol, PCMVolumeTransformer, FFmpegPCMAudio
from music_bot.song import Song
from music_bot.event_emitter import EventEmitter
import asyncio
from asyncio import AbstractEventLoop
import youtube_dl
from configuration import config
from json_logging import getLogger

logger = getLogger(__name__)

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

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
    'options': '-vn'
}

FFMEPG_PATH = config['ffmpeg_executable_path']

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

DEFAULT_QUEUE_DISPLAY_LIMIT = 10

class YTDLSource(PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls: PCMVolumeTransformer, url: str, *, loop=None) -> PCMVolumeTransformer:
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        return cls(FFmpegPCMAudio(data['url'], executable=FFMEPG_PATH, **ffmpeg_options), data=data)
    
    @classmethod
    async def from_song(cls: PCMVolumeTransformer, song: Song, *, loop=None) -> PCMVolumeTransformer:
        return await YTDLSource.from_url(song.url, loop=loop)

class AudioPlayerState(Enum):
    STOPPED = 0
    PLAYING = 1
    PAUSED = 2
    WAITING = ( 3 )
    DEAD = 4

    def __str__(self):
        return self.name

class AudioPlayer(EventEmitter):
    def __init__(self, loop: AbstractEventLoop, voice_client: VoiceProtocol):
        super(AudioPlayer, self).__init__()
        self.loop = loop
        self.voice_client = voice_client
        self._current_player = None
        self._source = None
        self._play_lock = asyncio.Lock()
        self._queue_lock = asyncio.Lock()
        self.queue = []

    async def get_yt_song(self, arg) -> Song:
        try:
            # TODO - Handle Playlists
            # TODO - Better validation than simple 'get' for youtube links, extracted from here
            get(arg)
            return Song(ytdl.extract_info(arg, download=False))
        except:
            return Song(ytdl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0])

    async def shuffle(self):
        async with self._queue_lock:
            shuffle(self.queue)

    async def remove_from_queue(self, pos):
        async with self._queue_lock:
            if (await self.is_queue_empty()):
                return

            if pos <= len(self.queue):
                del self.queue[pos-1]
            else:
                return

    async def add_to_queue(self, args):
        song = await self.get_yt_song(args)
        async with self._queue_lock:
            self.queue.insert(0, song)
            logger.debug(f'Added song \"{song.title}\" to the back of the queue')
    
    async def clear_queue(self):
        async with self._queue_lock:
            self.queue.clear()
    
    async def view_queue(self):
        async with self._queue_lock:
            if (await self.is_queue_empty()):
                return 'The Queue is Empty'

            queue_title = '**The Queue**'
            queue_breakln = '-' * 14
            queue = ''
            queue_display_limit = min(len(self.queue), DEFAULT_QUEUE_DISPLAY_LIMIT)
            highest_number_spacing = len(str(queue_display_limit))
            songs_in_queue = ''
            for pos, song in enumerate(self.queue[:queue_display_limit]):
                whitespace_buffer = ' ' * ((highest_number_spacing - len(str(pos + 1))) + 1)
                songs_in_queue += f'#{pos + 1}{whitespace_buffer}| ***{song.title}***\n'
            trailing = '...' if len(self.queue) > DEFAULT_QUEUE_DISPLAY_LIMIT else ''
            queue = f'>>> {songs_in_queue}{trailing}'
            return f'{queue_title}\n{queue_breakln}\n{queue}'

    
    async def _add_priority_song(self, args):
        song = await self.get_yt_song(args)
        async with self._queue_lock:
            logger.debug(f'Added song \"{song.title}\" to the front of the queue')
            self.queue.append(song)

    async def _getNextSong(self):
        async with self._queue_lock:   
            if (await self.is_queue_empty()):
                logger.debug('No new song in the queue, returning None')
                return None

            return self.queue.pop()

    def stop(self):
        logger.debug('Stopping Current player')
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
                logger.error('OSEror encountered in attempt to stop current player')
                pass
            self._current_player = None
            self._source.cleanup()
            self._source = None
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
        return self._current_player and self.voice_client.is_playing()

    async def playNext(self):
        logger.debug('In the play Next Function')
        nextSong = await self._getNextSong()
        logger.debug('Got the next Song (if there is one)')

        if (not nextSong): 
            logger.debug('No new song to play')
            self.stop()
            return            

        logger.debug(f'Next Song to play is {nextSong.title}')
        async with self._play_lock:
            if (self._current_player):
                logger.debug('Stopping current player to play next song')
                self.stop()
            self._source = await YTDLSource.from_song(nextSong, loop=self.loop)
            self.voice_client.play(self._source, after=self._on_player_complete)
            self._current_player = self.voice_client
            logger.info(f'Playing new song: {self._source.title}')

        self.emit('play')

    async def play(self, args):
        logger.debug('Inside play function')
        if self.is_paused() and self._current_player:
            return self.resume()

        if (self.is_playing()):
            async with self._play_lock:
                logger.debug('Request to play new song while player is playing. Stopping existing player')
                self.stop()

        await self._add_priority_song(args)
        await self.playNext()
        
    async def is_queue_empty(self):
        return len(self.queue) == 0

    def _on_player_complete(self, error=None):
        if (error):
            return

        self.emit('song-complete', player=self)