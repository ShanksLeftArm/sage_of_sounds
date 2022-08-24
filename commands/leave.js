const { getVoiceConnection } = require('@discordjs/voice');

module.exports = {
    name: 'leave',
    description: 'Stops playing of music and leaves a voice channel',
    async execute(client, message, args, Discord) {
        const voiceChannel = message.member.voice.channel;

        if (!voiceChannel) return message.channel.send('You are not a member of my audience! Try joining the voice channel where I am performing to stop my performance.');

        const connection = getVoiceConnection(voiceChannel.guild.id);
        if (!connection) return message.reply('I am not performing anywhere!');

        await connection.destroy();
        await message.reply('Closing up this performance. Farewell my friends. Until next time!');
    }
}