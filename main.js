const Discord = require('discord.js');
const Client = Discord.Client;
const GatewayIntentBits = Discord.GatewayIntentBits;
const { token } = require('./config.json')
const fs = require('fs');

const partials = [ "MESSAGE", "CHANNEL", "REACTION" ];
const client = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent, GatewayIntentBits.GuildVoiceStates], partials: partials});
const botName = 'SageOfSounds';
const prefix = '*';


client.once('ready', ()=> {
    console.log('SageOfSounds in online...');
    client.application.commands = new Discord.Collection();
    client.application.events = new Discord.Collection();

    ['command_handler', 'event_handler'].forEach(handler =>{
        require(`./handlers/${handler}`)(client, Discord);
    })
});


// client.on('messageCreate', message => {
//     if (!message.content.startsWith(prefix) || message.author.bot) return;

//     const args = message.content.slice(prefix.length).split(/ +/);
//     const command = args.shift();
//     const commandID = command.toLowerCase();
//     if (commandID in commands) {
//         commands[commandID].execute(message, args);
//     } else {
//         console.log(`Command \'${command}\' is not known to ${botName}`);
//         return message.reply(`Your instruction of \'${command}\' is not something I know how to do`);
//     }
// })

client.login(token);