const { Client, GatewayIntentBits } = require('discord.js');
const { token } = require('./config.json')
const fs = require('fs');

const botName = 'SageOfSounds';
const prefix = '*';

const client = new Client({ intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMessages, GatewayIntentBits.MessageContent, GatewayIntentBits.GuildVoiceStates]});

const commandFiles = fs.readdirSync('./commands/').filter(file => file.endsWith('.js'));
var commands = {};

for (const file of commandFiles) {
    const command = require(`./commands/${file}`);

    commands[command.name] =  command;
}

client.once('ready', () => {
    console.log('SageOfSounds in online...');
});

client.on('messageCreate', message => {
    if (!message.content.startsWith(prefix) || message.author.bot) return;

    const args = message.content.slice(prefix.length).split(/ +/);
    const command = args.shift();
    const commandID = command.toLowerCase();
    if (commandID in commands) {
        commands[commandID].execute(message, args);
    } else {
        console.log(`Command \'${command}\' is not known to ${botName}`);
        return message.reply(`Your instruction of \'${command}\' is not something I know how to do`);
    }
})

client.login(token);