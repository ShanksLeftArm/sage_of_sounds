const { joinVoiceChannel, createAudioPlayer, createAudioResource, getVoiceConnection, AudioPlayerStatus } = require('@discordjs/voice');
const { Message, Guild, VoiceChannel, TextChannel } = require('discord.js');
const { EventEmitter } = require('events');

class Song {
    constructor(title, url) {
        this.title = title;
        this.url = url;
    }

    get title() { return this.title; }
    get url() { return this.url; }
}

class Session {
    /**
     * Initializes a Session using Discord Message Obj
     * @param {DiscordMessage} message 
     */
    constructor(message) {
        if (!(message instanceof Message)) { throw 'Parameter is not a discord message'; }
        this.guild = message.guild;
        this.voice_channel = message.member.voice.channel;
        this.text_channel = message.channel;
        this.connection = null;
    }
    
    // constructor(guild, text_channel, voice_channel) {
    //     if (!(guild instanceof Guild)) { throw 'Expected instance of Guild in first param'; }
    //     if (!(text_channel instanceof TextChannel)) { throw 'Expected instance of TextChannel in first param'; }
    //     if (!(voice_channel instanceof VoiceChannel)) { throw 'Expected instance of VoiceChannel in first param'; }

    //     this.guild = guild;
    //     this.voice_channel = voice.channel;
    //     this.text_channel = text_channel;
    //     this.connection = null;
    // }

    get guild() { return this.guild; }
    get voiceChannel() { return this.voice_channel; }
    get textChannel() { return this.text_channel; }
    get connection() { return this.connection; }
    
    connect(player) {
        try {
            const connection = joinVoiceChannel({
                channelId: this.voice_channel.id,
                guildId: this.voice_channel.guild.id,
                adapterCreator: this.voice_channel.guild.voiceAdapterCreator,
            });
            connection.subscribe(player);
            this.connection = connection;
        } catch (err) {
            this.text_channel.channel.send('There was an error connecting to the voice channel...');
            throw err;
        } 
    }

    disconnect() {
        this.connection.destroy();
        this.connection = null;
    }
}

class ServerMusicQueue extends EventEmitter {
    constructor(message) {
        if (!(message instanceof Message)) { throw 'Parameter is not a discord message'; }
        this.songs = [];

        this.player = this.#createPlayer();
        this.session = new Session(message);
        this.session.connect(player);
    }

    // constructor(guild, text_channel, voice_channel) {
    //     if (!(guild instanceof Guild)) { throw 'Expected instance of Guild in first param'; }
    //     if (!(text_channel instanceof TextChannel)) { throw 'Expected instance of TextChannel in first param'; }
    //     if (!(voice_channel instanceof VoiceChannel)) { throw 'Expected instance of VoiceChannel in first param'; }
        
    //     this.songs = [];

    //     this.player = this.#createPlayer();
    //     this.session = new Session(guild, text_channel, voice_channel);
    //     this.session.connect(player);
    // } 

    queueSong = function(song) {
        if (!(song instanceof Song)) { throw 'Expected instance of Song '};
        this.songs.push(song);
        if (this.#isPaused()){
            this.playNextSong();
            this.session.text_channel.send(`I shall play you the song ***${song.title}***`);
        } else {
            this.session.text_channel.send(`I have recieved your request, will be playing ***${song.title}*** soon! Stick around.`);
        }
    }

    playSong = function(song) {
        if (!(song instanceof Song)) { throw 'Expected instance of Song '};
        const resource = this.#setupAudioResourceStream(song);
        this.session.text_channel.send(`I shall play you the song ***${song.title}***`);
        this.player.play(resource);
    }

    clearQueue = function() {
        this.songs = [];
    }

    playNextSong = function() {
        var nextResource = this.#getNextResource();
        if (!nextResource) {
            // TODO - add timeout until it destroys
            this.text_channel.send('Looks like I have no more requests, I bid you farewell!');
            this.destroy();
            return;
        }
        this.player.play(nextResource);
    }

    destroy = function() {
        this.player.stop();
        this.emit('destroy');
        this.session.disconnect();
    }

    #getNextResource = function(){
        const song = this.songs.pop();
        if (!song) return null;
    
        const resource = this.#setupAudioResourceStream(song);
        return resource;
    }

    #setupAudioResourceStream = function(song) {
        const stream = ytdl(song.url, {filter: 'audioonly'});
        const resource = createAudioResource(stream);
        return resource;
    }

    #isPaused = function(status) {
        return [AudioPlayerStatus.Paused, AudioPlayerStatus.AutoPaused, AudioPlayerStatus.Idle].includes(status);
    }   

    #createPlayer = function() {
        const player = createAudioPlayer();
        Object.values(AudioPlayerStatus).forEach((status) => {
            player.on(status, () => {
                console.log(STATUS_CHANGE_LOG(`Audio Player Status`, status));
            });
        });
        
        player.on(AudioPlayerStatus.Idle, () => {    
            this.playNextSong();
        });

        return player;
    }
}

class ServerMusicManager {
    constructor() {
        this.audioQueues = new Map();
    }

     getGuildQueue = async function(message) {
        if (!(message instanceof Message)) { throw 'Parameter is not a discord message'; }
        const guildId = message.guild.guildId;

        return this.audioQueues.get(guildId);
    }

    setupGuildQueue = async function(message) {
        const guildId = message.guild.guildId;
        var guildQueue = new ServerMusicQueue(message);
        guildQueue.on('destroy', () => {
            this.audioQueues.delete(guildId)
        });
        
        this.audioQueues.set(guildId, guildQueue);
        return guildQueue;
    }
}

module.exports = {
    name: 'ServerQueue',
    MusicManager: new ServerMusicManager()
}