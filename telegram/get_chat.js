TelegramBot = require('node-telegram-bot-api')

const bot = new TelegramBot(process.env.TM_TOKEN, {
  polling: true,
});

bot.onText(/chat id/, msg => bot.sendMessage(msg.chat.id, msg.chat.id))
