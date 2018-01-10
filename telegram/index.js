TelegramBot = require('node-telegram-bot-api')
emoji = require('node-emoji')

const bot = new TelegramBot(process.env.TM_TOKEN, {
  polling: false,
});

// change polling to true, so you will get chat id from bot
msg = emoji.emojify(process.env.MSG)

msg && bot.sendMessage(process.env.CHAT, msg, {
  disable_notification: true,
  parse_mode: 'Markdown'
})

// AU17: -1001143231884
// DD17:   -239361319
// demiurg906: 80632604
