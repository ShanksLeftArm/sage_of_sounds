from requests import get
import discord
from discord import Message
from discord.ext import commands
from music_bot.player import AudioPlayer
import json
import asyncio
import youtube_dl

class MusicBot(commands.Bot):
    def __init__(self, command_prefix, intents):
        commands.Bot.__init__(self, command_prefix=command_prefix, intents=intents)
        self.AudioPlayers = {}
        return 

    async def on_ready(self):
        print('Logged in!')
        await self.add_cog(BotCommands(self))

    
    async def get_audio_player(self, voice_channel):
        guild = voice_channel.guild
        if guild.id in self.AudioPlayers:
            return self.AudioPlayers[guild.id]

        if guild.voice_client is None:
            await voice_channel.connect()
            # await voice_channel.guild.change_voice_state(
            #     channel=voice_channel, self_mute=False, self_deaf=True
            # )
        
        newPlayer = self.init_player(AudioPlayer(self, guild.voice_client))
        self.AudioPlayers[guild.id] = newPlayer
        return newPlayer

    def init_player(self, player: AudioPlayer):
        player = (
            player.on('song-complete', self.on_player_complete)
        )

        return player

    async def on_player_complete(self, player, **__):
        # TODO empty VC logic
        # TODO empty playlist logic
        
        player.play()
        return

class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='add')
    async def add(self, ctx: commands.Context, *, args):
        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not anywhere I can perform my music! Try joining a voice channel')
            return

        player = await self.bot.get_audio_player(voiceState.channel)
        
        await player.add_to_queue(args)
        return
    
    @commands.command(name='play')
    async def play(self, ctx: commands.Context, *, args):
        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not anywhere I can perform my music! Try joining a voice channel')
            return

        player = await self.bot.get_audio_player(voiceState.channel)
        
        if (await player.is_queue_empty()):
            await player.add_to_queue(args)
            player.play()
        else:
            await player.add_to_queue(args)

    
    @commands.command(name='pause')
    async def pause(self, ctx: commands.Context):
        if (not ctx.voice_client):
            return

        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not anywhere I can perform my music! Try joining a voice channel')
            return

        player = await self.bot.get_audio_player(voiceState.channel)
        player.pause()

    @commands.command(name='resume')
    async def resume(self, ctx: commands.Context):
        if (not ctx.voice_client):
            return

        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not anywhere I can perform my music! Try joining a voice channel')
            return

        player = await self.bot.get_audio_player(voiceState.channel)
        player.resume()

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
        player.kill()
        await ctx.voice_client.disconnect()
        del self.bot.AudioPlayers[ctx.guild.id]