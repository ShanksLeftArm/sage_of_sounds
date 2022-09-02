const ytdl = require('ytdl-core');
const ytSearch = require('yt-search');
const yts = require('yt-search');
const { joinVoiceChannel, createAudioPlayer, createAudioResource, getVoiceConnection, AudioPlayerStatus } = require('@discordjs/voice');
const CommandValidator = require('../handlers/utility/command_validation.js');

const queue = new Map();
module.exports = {
    name: 'play',
    aliases: ['skip', 'stop', 'add'],
    cooldown: 0,
    description: 'Joins and plays a video from youtube',
    async execute(client, message, cmd, args, Discord) {
        if (!CommandValidator.areTheyInAnAudience(message)) {
            return message.reply('You are not anywhere I can perform my music! Try joining a voice channel');
        }

        if (!CommandValidator.mayTheySpeakHere(message)) {
            return message.reply(`I\'m afraid you have not been permitted to hear my music in that channel. Speak to my manager`);
        }

        const voice_channel = message.member.voice.channel;
        var server_queue = queue.get(message.guild.id);
        // Alias for skip
        if (cmd === 'skip') {
            if (!server_queue) {
                return message.reply(`I\'m not currently playing anywhere, if you'd like a performance, try \'${this.name}\'`);
            }
            playNextSong(server_queue);
            return;
        }

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
                player: null,
                songs: []
            }

            queue.set(message.guild.id, queue_constructor);
            
            try {
                const connection = joinVoiceChannel({
                    channelId: voice_channel.id,
                    guildId: voice_channel.guild.id,
                    adapterCreator: voice_channel.guild.voiceAdapterCreator,
                });
                queue_constructor.connection = connection;

                const player = await setupAutoPlayer(queue_constructor);
                queue_constructor.player = player;
                queue_constructor.connection.subscribe(player);

                server_queue = queue_constructor;
            } catch (err) {
                queue.delete(message.guild.id);
                message.channel.send('There was an error connecting...');
                throw err;
            } 
        }
        
        server_queue.songs.push(song);

        if (isServerPaused(server_queue.player.state) || !(cmd === 'add')) {
            playNextSong(server_queue);    
            message.reply(`I shall play you the song ***${song.title}***`);
        } else {
            message.reply(`I have recieved your request, will be playing ***${song.title}*** soon! Stick around.`)
        }
    }
}

const setupAutoPlayer = async (song_queue) => {
    const player = createAudioPlayer();
    Object.values(AudioPlayerStatus).forEach((status) => {
        player.on(status, () => {
            console.log(STATUS_CHANGE_LOG(`Audio Player Status`, status));
        });
    });
    

    player.on(AudioPlayerStatus.Idle, () => {    
        playNextSong(song_queue);
    });

    player.on('stateChange', (oldState, newState) => {
        // console.log(STATE_CHANGE_LOG(`Audio Player`, oldState, newState));
    });
    
    return player;
}

// TODO throw into Shared Player Class with Constants File

const isServerPaused = (server_status) => {
    const pausedStatuses = [AudioPlayerStatus.Paused, AudioPlayerStatus.AutoPaused, AudioPlayerStatus.Idle];
    return pausedStatuses.includes(server_status.status);
}

const playNextSong = (server_queue) => {
    nextResource = getNextResource(server_queue);
    if (!nextResource) {
        server_queue.text_channel.send('Looks like I have no more requests, I bid you farewell!');
        const guildId = server_queue.voice_channel.guild.id;
        server_queue.connection.destroy();
        queue.delete(guildId);
        return; 
    }
    server_queue.player.play(nextResource);
}

const getNextResource = (song_queue) => {
    const song = song_queue.songs.pop();
    if (!song) return null;

    const resource = setupYtStream(song);
    return resource;
}

const setupYtStream = (song) => {
    const stream = ytdl(song.url, {filter: 'audioonly'});
    const resource = createAudioResource(stream);
    return resource;
}

const STATUS_CHANGE_LOG = (resource, status) => {
    return EVENT_LOG(resource, 'STATUS CHANGE', `${status}`);
}

const STATE_CHANGE_LOG = (resource, oldState, newState) => {
    return EVENT_LOG(resource, 'STATE CHANGE', `${oldState.name} to ${newState.name}`);
}

const EVENT_LOG = (resource, event_name, short_desc) => {
    return `[${resource} | ${event_name}] ${short_desc}`;
}