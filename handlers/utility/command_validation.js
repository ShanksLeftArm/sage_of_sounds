const { PermissionsBitField } = require('discord.js');

function mayTheySpeakHere(message) {
    if (!areTheyInAnAudience(message)) return false;

    const neccesaryUserPermissions = [PermissionsBitField.Flags.Connect, PermissionsBitField.Flags.Speak];

    const voiceChannel = message.member.voice.channel;
    const userPermissions = voiceChannel.permissionsFor(message.client.user);

    // User must have access to voice channel
    neccesaryUserPermissions.forEach(permission => {
        if (!userPermissions.has(permission)) {
            return false;
        } 
    });

    return true;
}

function areTheyInAnAudience(message) {    
    const voiceChannel = message.member.voice.channel;
    return voiceChannel
}

module.exports = {
    name: 'play',
    description: 'Joins and plays a video from youtube',
    mayTheySpeakHere,
    areTheyInAnAudience
}