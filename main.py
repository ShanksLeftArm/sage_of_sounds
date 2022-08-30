import discord
from discord import Message
from discord.ext import commands
from music_bot.musicBot import MusicBot
import json

config = None
with open('config.json') as f:
    config = json.load(f)

prefix = '!'

intents =discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = MusicBot(command_prefix='!', intents=intents)
bot.run(config['token'])
