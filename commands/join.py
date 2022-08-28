import discord
from discord import Message
from discord.ext import commands
import json

class Join(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='join')
    async def join(self, ctx, *, member: discord.Member = None):
        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not anywhere I can perform my music! Try joining a voice channel')
            return
        await voiceState.channel.connect()
        return

    @commands.command(name='leave')
    async def leaveVoiceChat(self, ctx, *, member: discord.Member = None):
        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply('You are not in any of my audiences...')
            return
        channel = voiceState.channel
        voiceClient = [voiceClient for voiceClient in ctx.bot.voice_clients if voiceClient.channel.id == channel.id][0]
        await voiceClient.disconnect()
        return