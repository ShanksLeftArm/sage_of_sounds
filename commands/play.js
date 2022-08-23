const ytdl = require('ytdl-core');
const ytSearch = require('yt-search');
const yts = require('yt-search');
const { PermissionsBitField } = require('discord.js');
const { joinVoiceChannel, createAudioPlayer, createAudioResource } = require('@discordjs/voice');

const necessaryUserPermissions = [PermissionsBitField.Flags.Connect, PermissionsBitField.Flags.Speak];

module.exports = {
    name: 'play',
    description: 'Joins and plays a video from youtube',
    async execute(message, args) {
        const voiceChannel = message.member.voice.channel;

        if (!voiceChannel) return message.reply('You are not anywhere I can perform my music! Try joining a voice channel');

        const userPermissions = voiceChannel.permissionsFor(message.client.user);

        // User must have access to voice channel
        necessaryUserPermissions.forEach(permission => {
            if (!userPermissions.has(permission)) {
                return message.reply(`I\'m afraid you have not been permitted to hear my music in ${voiceChannel.name}. Speak to my manager`);
            } 
        });

        if (!args.length) return message.reply('I cannot play without a request! Give me something to play like this \'*play In the Air Tonight\'');

        const connection = await joinVoiceChannel({
            channelId: voiceChannel.id,
	        guildId: voiceChannel.guild.id,
	        adapterCreator: voiceChannel.guild.voiceAdapterCreator,
        });

        const videoFinder = async (query) => {
            const videoResult = await ytSearch(query);

            return (videoResult.videos.length > 1) ? videoResult.videos[0] : null;
        }
        
        const video = await videoFinder(args.join(' '));

        if (video) {
            const stream = ytdl(video.url, {filter: 'audioonly'});

            const player = createAudioPlayer();
            const resource = createAudioResource(stream);
            connection.subscribe(player);
            
            player.play(resource);

            await message.reply(`:thumbsup: I shall play you the song ***${video.title}***`);
        } else {
            await message.reply('I do not know of that tune... Maybe try another request');
        }
    }
}