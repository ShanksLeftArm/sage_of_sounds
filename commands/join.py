from requests import get
import discord
from discord import Message
from discord.ext import commands
import json
import asyncio
import youtube_dl

from sage_of_sounds.event_emitter import EventEmitter

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
        return cls(discord.FFmpegPCMAudio(executable="C:/Program Files/ffmpeg/ffmpeg-2022-08-22-git-f23e3ce858-full_build/bin/ffmpeg.exe", source=filename, **ffmpeg_options), data=data)

class AudioPlayer(EventEmitter):
    def __init__(self, bot, voice_client):
        self.bot = bot
        self.voice_client = voice_client
        self.queue = []
        

    # def play(self, url):

    async def add_to_queue(self, url):
        self.queue.append(url)

    async def play(self, url):
        player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
        self.voice_client.play(player, after=self._on_player_complete)

    async def playNext(self):
        nextUrl = self.queue.pop()
        if (nextUrl):
           await self.play(nextUrl)

    async def _on_player_complete(self, error=None):
        if (error):
            return

        this.emit

class Join(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
    
    @commands.command(name='join')
    async def join(self, ctx: commands.Context, *, member: discord.Member = None):
        if (ctx.voice_client):
            return

        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not anywhere I can perform my music! Try joining a voice channel')
            return
        voiceClient = await voiceState.channel.connect()
        
        self.bot.AudioPlayers[ctx.guild.id] = AudioPlayer(self.bot, voiceClient)
        return

    @commands.command(name='leave')
    async def leaveVoiceChat(self, ctx: commands.Context, *, member: discord.Member = None):
        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not in any of my audiences...')
            return

        voiceClient = ctx.voice_client
        if (voiceClient is None):
            return
        
        if (voiceClient.is_playing()):
            voiceClient.stop()

        await voiceClient.disconnect()
        return

    @commands.command(name='play')
    async def play(self, ctx: commands.Context, *, args):
        print(f'args: {args}')
        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not in any of my audiences...')
            return

        if ctx.voice_client is None:
            return
        
        async with ctx.typing():
            url = self.get_yt_url(args)
            player = await self.bot.get_audio_player(ctx.guild.id)
            if (player):
                await player.play(url)
            else:
                return

        # await ctx.send(f'Now playing: {player.title}')

    @commands.command(name='add')
    async def add_to_queue(self, ctx: commands.Context, *, args):
        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not in any of my audiences...')
            return

        if ctx.voice_client is None:
            return
        
        async with ctx.typing():
            url = self.get_yt_url(args)
            player = await self.bot.get_audio_player(ctx.guild.id)
            if (player):
                await player.add_to_queue(url)

    def get_yt_url(self, arg):
        try:
            get(arg)
        except:
            return ydl.extract_info(f"ytsearch:{arg}", download=False)['entries'][0]['webpage_url']
        else:
            return arg

  
        

        

        

