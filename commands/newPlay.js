const ytdl = require('ytdl-core');
const ytSearch = require('yt-search');
const yts = require('yt-search');
const { joinVoiceChannel, createAudioPlayer, createAudioResource, getVoiceConnection, AudioPlayerStatus } = require('@discordjs/voice');
const CommandValidator = require('../handlers/utility/command_validation.js');

const queue = new Map();
module.exports = {
    name: 'newPlay',
    aliases: ['skip', 'stop'],
    cooldown: 0,
    description: 'Joins and plays a video from youtube',
    async execute(client, message, args, Discord) {
        
        if (!CommandValidator.areTheyInAnAudience(message)) {
            return message.reply('You are not anywhere I can perform my music! Try joining a voice channel');
        }

        if (!CommandValidator.mayTheySpeakHere(message)) {
            return message.reply(`I\'m afraid you have not been permitted to hear my music in that channel. Speak to my manager`);
        }

        const voice_channel = message.member.voice.channel;
        
        const server_queue = queue.get(message.guild.id);

        if (!args.length) return message.reply('I cannot play without a request! Give me something to play like this \'*play In the Air Tonight\'');
        let song = {};

        if (ytdl.validateURL(args[0])) {
            // TODO: Add Playlist Queueing Support
            const song_info = await ytdl.getInfo(args[0]);
            song = { title: song_info.videoDetails.title, url: song_info.videoDetails.video_url }
        } else {
            const videoFinder = async (query) => {
                const videoResult = await ytSearch(query);

                return (videoResult.videos.length > 1) ? videoResult.videos[0] : null;
            }
        
            const video = await videoFinder(args.join(' '));

            if (video) {
                song = { title: video.title, url: video.url }
            } else {
                await message.reply('I do not know of that tune... Maybe try another request');
            }
        }

        if (!server_queue) {
            const queue_constructor = {
                voice_channel: voice_channel,
                text_channel: message.channel,
                connection: null,
                songs: []
            }

            queue.set(message.guild.id, queue_constructor);
            
            try {
                const connection = await joinVoiceChannel({
                    channelId: voice_channel.id,
                    guildId: voice_channel.guild.id,
                    adapterCreator: voice_channel.guild.voiceAdapterCreator,
                });
                queue_constructor.connection = connection;

                const player = await setupAutoPlayer(queue_constructor);
                
                const resource = await setupYtStream(song);
                queue_constructor.connection.subscribe(player);

                player.play(resource);
                message.reply(`I shall play you the song **${song.title}**`);
            } catch (err) {
                queue.delete(message.guild.id);
                message.channel.send('There was an error connecting...');
                throw err;
            } 
        } else {
            server_queue.songs.push(song);
            return message.reply(`**${song.title}** added to the queue!`);
        }
    }
}

const getNextResource = async (song_queue) => {
    const song = song_queue.songs.pop();
    const resource = await setupYtStream(song);
    return resource;
}

const setupAutoPlayer = async (song_queue) => {
    const player = createAudioPlayer();

    player.on(AudioPlayerStatus.Idle, () => {
        if (song_queue.songs.length == 0) {
            song_queue.connection.destroy();
            queue.delete(guild.id);
            return; 
        }

        player.play(getNextResource(song_queue));
    });
    
    return player;
}

const setupYtStream = async (song) => {
    const stream = ytdl(song.url, {filter: 'audioonly'});
    const resource = createAudioResource(stream);
    return resource;
}