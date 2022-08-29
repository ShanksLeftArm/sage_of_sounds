import discord
from discord import Message
from discord.ext import commands
from commands.join import Join
import json

config = None
with open('config.json') as f:
    config = json.load(f)

prefix = '!'
class MyBot(commands.Bot):
    def __init__(self, command_prefix, intents):
        commands.Bot.__init__(self, command_prefix=command_prefix, intents=intents)
        self.AudioPlayers = {}
        return 

    async def on_ready(self):
        print('Logged in!')
        await self.add_cog(Join(self))

    async def get_audio_player(self, guildId):
        return self.AudioPlayers[guildId]


intents =discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = MyBot(command_prefix='!', intents=intents)
bot.run(config['token'])
