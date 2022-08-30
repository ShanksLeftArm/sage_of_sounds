from requests import get
import discord
from discord import Message
from discord.ext import commands
import json
import asyncio
import youtube_dl

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

  
        

        

        

