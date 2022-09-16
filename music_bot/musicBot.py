from requests import get
import discord
from discord import VoiceChannel
from discord.ext import commands
from music_bot.player import AudioPlayer
from music_bot.command_validation import MusicCommandValidation
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
        await self.add_cog(MusicCommands(self))

    
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
        logger.debug('Player Completed, playing next song')
        await player.playNext()
        logger.debug('Next Song Played. Ending on_player_complete')
        return

class MusicCommands(commands.Cog):
    def __init__(self, bot: MusicBot):
        self.bot = bot
        self.I_WILL_NOT_DO_THAT = 'You are not in my audience, I will not do that'
        self.YOU_ARE_NOT_IN_VOICE_CHAT = 'You are not anywhere I can perform my music! Try joining a voice channel'

    @commands.command(name='add')
    async def add(self, ctx: commands.Context, *, song_query):
        '''
        Adds a new song to be performed in the music queue

            add <search for youtube>
            add <youtube song url>
            
            Examples:
                add never gonna give you up lyrics
                add https://www.youtube.com/watch?v=dQw4w9WgXcQ
        '''
        if (MusicCommandValidation.authorIsInAudience(ctx)):
            player = await self.bot.get_audio_player(ctx.author.voice.channel)
            await player.add_to_queue(song_query)
            return
        elif (MusicCommandValidation.botIsNotPerforming(ctx)):
            return
        else:
            await ctx.message.reply(self.I_WILL_NOT_DO_THAT)
            return
        

    @commands.command(name='shuffle')
    async def shuffle(self, ctx: commands.Context):
        '''
        Shuffles the music queue
        '''
        if (MusicCommandValidation.authorIsInAudience(ctx)):
            player = await self.bot.get_audio_player(ctx.author.voice.channel)
            await player.shuffle()
            return
        elif (MusicCommandValidation.botIsNotPerforming(ctx)):
            return
        else:
            await ctx.message.reply(self.I_WILL_NOT_DO_THAT)
            return

    @commands.command(name='remove')
    async def remove(self, ctx: commands.Context, *, position):
        '''
        Removes a specified song from the music queue by position. 1 is the next song

            remove <number for song in queue>

            Examples:
                remove 1
                remove 4
        '''
        if (MusicCommandValidation.authorIsInAudience(ctx)):
            try:
                pos = int(position)
                player = await self.bot.get_audio_player(ctx.author.voice.channel)

                player = await self.bot.get_audio_player(ctx.author.voice.channel)
                await player.remove_from_queue(pos)
                return
            except Exception as e:
                logger.error(f'Position Argument was not integer: {e.__name__}')
                await ctx.send(f'If you would like to remove something from the list, try passing me a number to represent the position of the song you would like to remove. Try the \'queue\' command to see the current queue')
                return 
        elif (MusicCommandValidation.botIsNotPerforming(ctx)):
            return
        else:
            await ctx.message.reply(self.I_WILL_NOT_DO_THAT)
            return
       
    
    @commands.command(name='clear')
    async def clear(self, ctx: commands.Context):
        '''
        Clears the current music queue
        '''
        if (MusicCommandValidation.authorIsInAudience(ctx)):
            player = await self.bot.get_audio_player(ctx.author.voice.channel)
            await player.clear_queue()
            return
        elif (MusicCommandValidation.botIsNotPerforming(ctx)):
            return
        else:
            await ctx.message.reply(self.I_WILL_NOT_DO_THAT)
            return
        
    @commands.command(name='play')
    async def play(self, ctx: commands.Context, *, song_query):
        '''
        Begins a new performance for the requested song

            play <search for youtube>
            play <youtube song url>

            Examples:
                play never gonna give you up lyrics
                play https://www.youtube.com/watch?v=dQw4w9WgXcQ
        '''
        
        voiceState = ctx.author.voice
        if (voiceState is None):
            await ctx.message.reply(self.YOU_ARE_NOT_IN_VOICE_CHAT)
            return

        player = await self.bot.get_audio_player(voiceState.channel)
        
        await player.play(song_query)
        logger.debug('Play command complete')
        return

    @commands.command(name='stop')
    async def stop(self, ctx: commands.Context):
        '''
        Pauses the current performance 
        '''
        logger.debug('Stop command started')
        await self.__pause()        
        logger.debug('Stop command complete')
        return
    
    @commands.command(name='pause')
    async def pause(self, ctx: commands.Context):
        '''
        Pauses the current performance 
        '''
        logger.debug('Pause command started')
        await self.__pause(ctx)
        logger.debug('Pause command ended')
        return
    
    async def __pause(self, ctx: commands.Context):
        if (MusicCommandValidation.authorIsInAudience(ctx)):
            player = await self.bot.get_audio_player(ctx.author.voice.channel)
            await player.pause()
        elif (MusicCommandValidation.botIsNotPerforming(ctx)):
            pass
        else:
            await ctx.message.reply(self.I_WILL_NOT_DO_THAT)
        return


    @commands.command(name='resume')
    async def resume(self, ctx: commands.Context):
        '''
        Resumes play if a performance was paused
        '''
        logger.debug('Resume command started')
        await self.__resume(ctx)
        logger.debug('Resume command ended')
        return
        

    async def __resume(self, ctx: commands.Context):
        if (MusicCommandValidation.authorIsInAudience(ctx)):
            player = await self.bot.get_audio_player(ctx.author.voice.channel)
            await player.resume()
        elif (MusicCommandValidation.botIsNotPerforming(ctx)):
            pass
        else:
            await ctx.message.reply(self.I_WILL_NOT_DO_THAT)

        return

    @commands.command(name='next')
    async def next(self, ctx: commands.Context):
        '''
        Stops the current performance and begins the next in the music queue
        '''
        logger.debug('Next command started')
        await self.__skip_song(ctx)
        logger.debug('Next command ended')
        return 
    
    @commands.command(name='skip')
    async def skip_song(self, ctx: commands.Context):
        '''
        Stops the current performance and begins the next in the music queue
        '''
        logger.debug('Skip Song command started')
        await self.__skip_song(ctx)
        logger.debug('Skip Song command ended')
        return

    async def __skip_song(self, ctx: commands.Context):
        if (MusicCommandValidation.authorIsInAudience(ctx)):
            player = await self.bot.get_audio_player(ctx.author.voice.channel)
            await player.playNext()
            return
        elif (MusicCommandValidation.botIsNotPerforming(ctx)):
            pass
        else:
            await ctx.message.reply(self.I_WILL_NOT_DO_THAT)
        return
    
    @commands.command(name='now_playing')
    async def now(self, ctx: commands.Context):
        '''
        Displays what song is currently being performed
        '''
        logger.debug('now_playing command started')
        await self.__now_playing(ctx)
        logger.debug('now_playing command ended')
        return

    @commands.command(name='whats_playing')
    async def now(self, ctx: commands.Context):
        '''
        Displays what song is currently being performed
        '''
        logger.debug('whats_playing command started')
        await self.__now_playing(ctx)
        logger.debug('whats_playing command ended')
        return
    
    @commands.command(name='now')
    async def now(self, ctx: commands.Context):
        '''
        Displays what song is currently being performed
        '''
        logger.debug('Now command started')
        await self.__now_playing(ctx)
        logger.debug('Now command ended')
        return

    async def __now_playing(self, ctx: commands.Context):
        if (MusicCommandValidation.authorIsInAudience(ctx)):
            player = await self.bot.get_audio_player(ctx.author.voice.channel)
            now_playing_message = await player.get_now_playing()
            if (now_playing_message):
                await ctx.send(f'{now_playing_message}')
            else:
                await ctx.send('I am not currently playing - ask me to play something')
            return
        elif (MusicCommandValidation.botIsNotPerforming(ctx)):
            pass
        else:
            await ctx.message.reply(self.I_WILL_NOT_DO_THAT)
        return

    @commands.command(name='join')
    async def join(self, ctx: commands.Context):
        '''
        Request for me to join your voice channel for a performance
        '''
        if (MusicCommandValidation.botIsNotPerforming(ctx)):
            if (ctx.author.voice):
                await self.bot.get_audio_player(ctx.author.voice.channel)
            else:
                await ctx.reply(self.YOU_ARE_NOT_IN_VOICE_CHAT)
        return
    
    @commands.command(name = 'leave')
    async def leave(self, ctx: commands.Context):
        '''
        Request for me stop performing and to leave your voice channel
        '''        
        if (MusicCommandValidation.authorIsInAudience(ctx)):
            player = await self.bot.get_audio_player(ctx.author.voice.channel)
            await player.kill()
            await ctx.voice_client.disconnect()
            del self.bot.AudioPlayers[ctx.guild.id]
        elif (MusicCommandValidation.botIsNotPerforming(ctx)):
            pass
        else:
            await ctx.reply(self.I_WILL_NOT_DO_THAT)
        
        return
        

    @commands.command('queue')
    async def queue(self, ctx: commands.Context):
        '''
        Displays what is currently playing and what is in the queue
        '''
        if (MusicCommandValidation.authorIsInAudience(ctx)):
            player = await self.bot.get_audio_player(ctx.author.voice.channel)
            queue_message = await player.view_queue()
            await ctx.send(queue_message)
        elif (MusicCommandValidation.botIsNotPerforming(ctx)):
            pass
        else:
            pass
        
        return

    @commands.command('volume')
    async def volume(self, ctx: commands.Context, *, volume_adjustment: str):
        '''
        Request to view or adjust the current volume

            volume display
            volume up
            volume down
            volume <number between 1 and 100>
        
            Examples:
                volume display
                volume 35
                volume up

        '''
        if (MusicCommandValidation.authorIsInAudience(ctx)):
            command_option = volume_adjustment.split(" ")[0]
            player = await self.bot.get_audio_player(ctx.author.voice.channel)

            if (command_option.isnumeric()):
                new_volume = int(command_option)
                if 1 <= new_volume or new_volume <= 100:
                    await player.set_volume(new_volume)
                else:
                    await ctx.send(f'{command_option} is an invalid volume. Numbers between 1-100 are accepted')                
            elif (command_option.lower() == 'display'):
                volume = await player.get_volume()
                if (volume):
                    await ctx.send(f'Playing at {volume}% volume')
                else:
                    logger.error('Volume is null despite performance in progress in guild {} (ID {})'.format(ctx.guild.name, ctx.guild.id))
            elif (command_option.lower() in ['up', 'down']):
                await player.volume_adjustment(command_option.lower())
            else:
                await ctx.send(f'I do not recognize your volume request \'{command_option}\'. Try a number between 1 and 100, \'up\' or \'down\', or \'display\' to see the current volume')
        elif (MusicCommandValidation.botIsNotPerforming(ctx)):
            pass
        else:
            await ctx.reply(self.I_WILL_NOT_DO_THAT)
        
        return
