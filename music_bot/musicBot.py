from requests import get
import discord
from discord import VoiceChannel
from discord.ext import commands
from music_bot.player import AudioPlayer
import json
import asyncio
import youtube_dl

from json_logging import getLogger

logger = getLogger(__name__)

class MusicBot(commands.Bot):
    def __init__(self, command_prefix, intents):
        commands.Bot.__init__(self, command_prefix=command_prefix, intents=intents)
        self.AudioPlayers = {}
        return 

    async def on_ready(self):
        print('Logged in!')
        await self.add_cog(BotCommands(self))

    
    async def get_audio_player(self, voice_channel: VoiceChannel):
        guild = voice_channel.guild
        if guild.id in self.AudioPlayers:
            return self.AudioPlayers[guild.id]

        if guild.voice_client is None:
            await voice_channel.connect()
            # await voice_channel.guild.change_voice_state(
            #     channel=voice_channel, self_mute=False, self_deaf=True
            # )
        
        newPlayer = self.init_player(AudioPlayer(self.loop, guild.voice_client))
        self.AudioPlayers[guild.id] = newPlayer
        return newPlayer

    def init_player(self, player: AudioPlayer):
        player = (
            player.on('song-complete', self.on_player_complete)
        )

        return player

    async def on_player_complete(self, player: AudioPlayer, **__):
        # TODO empty VC logic
        logger.debug('Player Completed, playing next song')
        await player.playNext()
        logger.debug('Next Song Played. Ending on_player_complete')
        return

class BotCommands(commands.Cog):
    def __init__(self, bot: MusicBot):
        self.bot = bot

    @commands.command(name='add')
    async def add(self, ctx: commands.Context, *, args):
        if (not ctx.voice_client):
            return

        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not anywhere I can perform my music! Try joining a voice channel')
            return

        player = await self.bot.get_audio_player(voiceState.channel)
        
        await player.add_to_queue(args)
        return

    @commands.command(name='shuffle')
    async def shuffle(self, ctx: commands.Context):
        if (not ctx.voice_client):
            return

        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not anywhere I can perform my music! Try joining a voice channel')
            return
        
        player = await self.bot.get_audio_player(voiceState.channel)
        
        await player.shuffle()
        return

    @commands.command(name='remove')
    async def remove(self, ctx: commands.Context, *, args):
        if (not ctx.voice_client):
            return

        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not anywhere I can perform my music! Try joining a voice channel')
            return

        try:
            pos = int(args)
        except Exception as e:
            logger.error(f'Position Argument was not integer: {e.__name__}')
            await ctx.send(f'If you would like to remove something from the list, try passing me a number to represent the position of the song you would like to remove. Try the \'queue\' command to see the current queue')
            return 
        
        player = await self.bot.get_audio_player(voiceState.channel)
        await player.remove_from_queue(pos)
        return
    
    @commands.command(name='clear')
    async def clear(self, ctx: commands.Context):
        if (not ctx.voice_client):
            return

        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not anywhere I can perform my music! Try joining a voice channel')
            return
        
        player = await self.bot.get_audio_player(voiceState.channel)
        await player.clear_queue()
        return
        
    @commands.command(name='play')
    async def play(self, ctx: commands.Context, *, args):
        logger.debug('Play command started')
        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not anywhere I can perform my music! Try joining a voice channel')
            return

        player = await self.bot.get_audio_player(voiceState.channel)
        
        await player.play(args)
        logger.debug('Play command complete')
        return

    @commands.command(name='stop')
    async def stop(self, ctx: commands.Context):
        logger.debug('Stop command started')
        
        if (not ctx.voice_client):
            return

        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not anywhere I can perform my music! Try joining a voice channel')
            return
        
        player = await self.bot.get_audio_player(voiceState.channel)
        await player.stop()
        logger.debug('Stop command complete')
        return
    
    @commands.command(name='pause')
    async def pause(self, ctx: commands.Context):
        logger.debug('Pause command started')
        await self._pause(ctx)
        logger.debug('Pause command ended')
        return
    
    async def _pause(self, ctx: commands.Context):
        if (not ctx.voice_client):
            logger.debug('Play command complete')
            return

        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not anywhere I can perform my music! Try joining a voice channel')
            return

        player = await self.bot.get_audio_player(voiceState.channel)
        await player.pause()


    @commands.command(name='resume')
    async def resume(self, ctx: commands.Context):
        logger.debug('Resume command started')
        await self._resume(ctx)
        logger.debug('Resume command ended')
        return
        

    async def _resume(self, ctx: commands.Context):
        if (not ctx.voice_client):
            return

        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not anywhere I can perform my music! Try joining a voice channel')
            return

        player = await self.bot.get_audio_player(voiceState.channel)
        await player.resume()
        return
    
    @commands.command(name='next')
    async def next(self, ctx: commands.Context):
        logger.debug('Next command started')
        await self._skip_song(ctx)
        logger.debug('Next command ended')
        return 
    
    @commands.command(name='skip')
    async def skip_song(self, ctx: commands.Context):
        logger.debug('Skip Song command started')
        await self._skip_song(ctx)
        logger.debug('Skip Song command ended')
        return

    async def _skip_song(self, ctx: commands.Context):
        if (not ctx.voice_client):
            return
        
        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not anywhere I can perform my music! Try joining a voice channel')
            return
        
        player = await self.bot.get_audio_player(voiceState.channel)
        await player.playNext()
        return
        

    @commands.command(name='join')
    async def join(self, ctx: commands.Context, *, member: discord.Member = None):
        if (ctx.voice_client):
            return

        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not anywhere I can perform my music! Try joining a voice channel')
            return
        
        await self.bot.get_audio_player(voiceState.channel)
        return
    
    @commands.command(name = 'leave')
    async def leave(self, ctx: commands.Context, *, member: discord.Member = None):
        if (not ctx.voice_client):
            return
        
        voiceState = ctx.author.voice
        if (voiceState is None):
            return
        
        player = await self.bot.get_audio_player(voiceState.channel)
        await player.kill()
        await ctx.voice_client.disconnect()
        del self.bot.AudioPlayers[ctx.guild.id]
        return

    @commands.command('queue')
    async def queue(self, ctx: commands.Context):
        if (not ctx.voice_client):
            return
        
        voiceState = ctx.author.voice
        if (voiceState is None):
            return


        player = await self.bot.get_audio_player(voiceState.channel)
        queue_message = await player.view_queue()
        await ctx.send(queue_message)
        return 
