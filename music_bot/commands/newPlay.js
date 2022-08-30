const ytdl = require('ytdl-core');
const ytSearch = require('yt-search');
const yts = require('yt-search');
const { joinVoiceChannel, createAudioPlayer, createAudioResource, getVoiceConnection, AudioPlayerStatus } = require('@discordjs/voice');
const CommandValidator = require('../handlers/utility/command_validation.js');
const MusicManager = require('../performance/server_queue.js').MusicManager;

const queue = new Map();
module.exports = {
    name: 'newPlay',
    async execute(client, message, cmd, args, Discord) {
        if (!CommandValidator.areTheyInAnAudience(message)) {
            return message.reply('You are not anywhere I can perform my music! Try joining a voice channel');
        }

        if (!CommandValidator.mayTheySpeakHere(message)) {
            return message.reply(`I\'m afraid you have not been permitted to hear my music in that channel. Speak to my manager`);
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

        var guildQueue = MusicManager.getGuildQueue(message);
        if (!guildQueue) {
            guildQueue = MusicManager.setupGuildQueue(message);
        }

        guildQueue.playSong(song);
    }
}