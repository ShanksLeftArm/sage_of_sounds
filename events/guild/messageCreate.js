const cooldowns = new Map();
module.exports = (Discord, client, message) => {
    const prefix = '*';
    if (!message.content.startsWith(prefix) || message.author.bot) return;

    const args = message.content.slice(prefix.length).split(/ +/);
    const cmd = args.shift();
    const bot_command = client.application.commands.get(cmd) || client.application.commands.find(a => a.aliases && a.aliases.includes(cmd));

    if (bot_command){
         bot_command.execute(client, message, cmd, args, Discord);
    } else {
        console.log(`Command \'${cmd}\' is not known to me`);
        return message.reply(`Your instruction of \'${cmd}\' is not something I know how to do`);
    }
   
    

}