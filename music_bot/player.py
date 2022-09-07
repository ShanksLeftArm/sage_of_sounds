from enum import Enum
from random import shuffle
from requests import get
from discord import VoiceProtocol, PCMVolumeTransformer, FFmpegPCMAudio, Embed
from music_bot.song import Song
from music_bot.event_emitter import EventEmitter
from music_bot.text_utils import formatSecondsToTime
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

DEFAULT_QUEUE_DISPLAY_LIMIT = 5

class YTDLSource(PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        self._source = source
        super().__init__(source, volume)
        
        self.count_20ms = 0
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.webpage_url = data.get('webpage_url')
        self._duration = data.get('duration')
        self.uploader = data.get('uploader')
        self.description = data.get('description')
        self.thumbnail_link = data.get('thumbnail')

    @classmethod
    async def from_url(cls: PCMVolumeTransformer, url: str, *, loop=None) -> PCMVolumeTransformer:
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        return cls(FFmpegPCMAudio(data['url'], executable=FFMEPG_PATH, **ffmpeg_options), data=data)
    
    @classmethod
    async def from_song(cls: PCMVolumeTransformer, song: Song, *, loop=None) -> PCMVolumeTransformer:
        return await YTDLSource.from_url(song.url, loop=loop)

    def read(self) -> bytes:
        data = self._source.read()
        if data:
            self.count_20ms += 1
        return data

    @property
    def progress(self) -> str:
        return formatSecondsToTime(int(self.count_20ms * 0.02))
    
    @property
    def duration(self) -> str:
        return formatSecondsToTime(int(self._duration))

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
            if (await self._is_queue_empty()):
                return

            if pos <= len(self.queue):
                del self.queue[pos-1]
            else:
                return

    async def add_to_queue(self, args):
        song = await self.get_yt_song(args)
        async with self._queue_lock:
            self.queue.append(song)
            logger.debug(f'Added song \"{song.title}\" to the back of the queue')
    
    async def clear_queue(self):
        async with self._queue_lock:
            self.queue.clear()
    
    async def view_queue(self):
        async with self._queue_lock:
            if (await self._is_queue_empty()):
                _now = await self._get_now_playing()
                now_playing = f'{_now}\n\n**EMPTY QUEUE**' if _now else 'Currently on break with no requests... Let me know if you want to play or queue up something'

                return now_playing

            queue_title = '**THE QUEUE**'
            queue_breakln = '-' * 14
            queue = ''
            queue_display_limit = min(len(self.queue), DEFAULT_QUEUE_DISPLAY_LIMIT)
            highest_number_spacing = len(str(queue_display_limit))
            songs_in_queue = ''
            for pos, song in enumerate(self.queue[:queue_display_limit]):
                whitespace_buffer = ' ' * ((highest_number_spacing - len(str(pos + 1))) + 1)
                songs_in_queue += f'#{pos + 1}{whitespace_buffer}| ***{song.title}*** | {song.duration}\n'
            trailing = '...' if len(self.queue) > DEFAULT_QUEUE_DISPLAY_LIMIT else ''
            queue = f'>>> {songs_in_queue}{trailing}'
            
            # Add Currently Playing if there is a current song
            _now = await self.get_now_playing()
            now_playing = f'{_now}\n\n' if _now else ''
            return f'{now_playing}{queue_title}\n{queue_breakln}\n{queue}'

    async def get_now_playing(self):
        async with self._play_lock:
            _now = await self._get_now_playing()
            return f'{_now}' if _now else 'There is no current song; I\'m on break at the moment. Let me know if you want to hear a tune'
    
    async def _get_now_playing(self):
        if (self._is_playing() or self._is_paused()) and self._source:
            paused_vs_play = 'NOW PAUSED' if self._is_paused() else 'NOW PLAYING'
            now_playing_breakln = '-' * 14
            return f'**{paused_vs_play}**\n{now_playing_breakln}\n***{self._source.title}***\n<{self._source.webpage_url}>\n{self._source.progress} / {self._source.duration}'
        else:
            return None

    async def _add_priority_song(self, args):
        song = await self.get_yt_song(args)
        async with self._queue_lock:
            self.queue.insert(0, song)
            logger.debug(f'Added song \"{song.title}\" to the front of the queue')
            

    async def _getNextSong(self):
        if (await self._is_queue_empty()):
            logger.debug('No new song in the queue, returning None')
            return None

        return self.queue.pop(0)
    
    async def stop(self):
        async with self._play_lock:
            logger.debug('Play Lock Acquired')
            self._stop()
        logger.debug('Play Lock Released')

    def _stop(self):
        logger.debug('Stopping Current player')
        self._kill_current_player()
        self.emit('stop')

    async def kill(self):
        async with self._queue_lock:
            self.queue.clear()
        async with self._play_lock:
            logger.debug('Play Lock Acquired')
            self._kill_current_player()
        logger.debug('Play Lock Acquired')
        return

    def _kill_current_player(self):
        if self._current_player:
            try:
                player_to_stop = self._current_player
                self._current_player = None
                player_to_stop.stop()
                self._source.cleanup()
                self._source = None
            except OSError:
                logger.error('OSEror encountered in attempt to stop current player')
                pass
            return True
        return False

    async def pause(self):
        async with self._play_lock:
            logger.debug('Play Lock Acquired')
            await self._pause()
        
        logger.debug('Play Lock Released')
        return
    
    async def _pause(self):
        if self._is_playing():
            self.voice_client.pause()

    async def resume(self):
        async with self._play_lock:
            logger.debug('Play Lock Acquired')
            await self._resume()
        logger.debug('Play Lock Released')
        return
            
    async def _resume(self):
        if self._is_paused() and self._current_player:
                self._current_player.resume()
                self.emit('resume')
                return
            
        if self._is_paused() and not self._current_player:
            self._kill_current_player()
            return
    
    def _is_paused(self):
        return self.voice_client.is_paused()
    
    def _is_playing(self):
        return self._current_player and self.voice_client.is_playing()

    async def playNext(self):
        async with self._play_lock:
            logger.debug('Play Lock Acquired')
            await self._playNext()
        logger.debug('Play Lock Released')
        return

    async def _playNext(self):
        logger.debug('In the play Next Function')
        if (self._current_player and self._current_player.is_playing()):
            logger.debug('Stopping current player to play next song')
            self._stop()
            return

        async with self._queue_lock:
            nextSong = await self._getNextSong()

        if (not nextSong): 
            logger.debug('No new song to play')
            self._stop()
            return            

        logger.debug(f'Next Song to play is {nextSong.title}')
        self._source = await YTDLSource.from_song(nextSong, loop=self.loop)
        self.voice_client.play(self._source, after=self._on_player_complete)
        self._current_player = self.voice_client
        logger.info(f'Playing new song: {self._source.title}')

        self.emit('play')
        return

    async def play(self, args):
        async with self._play_lock:
            logger.debug('Play Lock Acquired')
            if self._is_paused() and self._current_player:
                return self._resume()
            
            if (self._is_playing()):
                logger.debug('Request to play new song while player is playing. Stopping existing player')
                self._stop()

            await self._add_priority_song(args)
            await self._playNext()
        logger.debug('Play Lock Released')
        return
        
    async def _is_queue_empty(self):
        return len(self.queue) == 0

    def _on_player_complete(self, error=None):
        if (error):
            logger.error('There was an error on player completion', error)
            return

        logger.debug('No Error on player complete, emiting song-complete')
        self.emit('song-complete', player=self)
        return