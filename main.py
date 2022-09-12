import discord
from discord import Message
from discord.ext import commands
from music_bot.musicBot import MusicBot
import json
from configuration import config
from json_logging import getLogger

logger = getLogger(__name__)

prefix = '!'

intents =discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = MusicBot(command_prefix=config['command_prefix'], intents=intents)
try:
    bot.run(config['token'])
    logger.debug('bot is successfully running')
except Exception as e:
    logger.error('Error starting bot. Exception:' + e)