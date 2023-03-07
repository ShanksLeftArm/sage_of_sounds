import json
from argparse import Namespace, ArgumentParser
import sys

import discord
from discord import Message
from discord.ext import commands
from music_bot.musicBot import MusicBot

from configuration import config
from json_logging import getLogger

logger = getLogger(__name__)
INTENTS = discord.Intents.default()

def set_up() -> ArgumentParser: 
	parser = ArgumentParser()
	parser.add_argument('-t', '--test', action='store_true', help='enables testing configurations')
	parser.add_argument('-p', '--prefix', default='!', type=str, help='the command prefix to set, defaults to !')

	# Add Voice State Capability
	INTENTS.message_content = True
	INTENTS.voice_states = True

	return parser


def start_bot(prefix, test_mode):
	bot = MusicBot(command_prefix=prefix, intents=INTENTS)
	try:
		token = config['token']
		if (test_mode):
			logger.info('Runnig in test mode!!!!!')
			token = config['test_token']
		bot.run(token)
	except Exception as e:
		logger.error('Error starting bot. Exception:' + e)


if __name__ == '__main__':
	parser = set_up()
	args, unknown = parser.parse_known_args(sys.argv[1:])
	
	start_bot(prefix=args.prefix, test_mode=args.test)

