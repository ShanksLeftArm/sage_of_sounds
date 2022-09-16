from discord.ext import commands

class MusicCommandValidation:
    def __init__(self) -> None:
        pass

    @staticmethod 
    def botIsNotPerforming(ctx: commands.Context):
        # Validate Bot is Currently In VC
        return ctx.voice_client is None
    
    @staticmethod
    def authorIsInAudience(ctx: commands.Context):
        if (__class__.botIsNotPerforming(ctx)):
            return False
        
        authorVoiceState = ctx.author.voice
        if (authorVoiceState):
            return authorVoiceState.channel == ctx.voice_client.channel
        else:
            return False

    
