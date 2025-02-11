// index.js
const { Telegraf } = require('telegraf');
const config = require('./config/config.json');
const { handleStart, handleRegister } = require('./handlers/startHandler');
const { handleButton } = require('./handlers/buttonHandler');

const bot = new Telegraf(config.botToken);

bot.command('start', handleStart);
bot.action('register', handleRegister);
bot.action(['deposit', 'order', 'list', 'riwayat', 'reffil', 'cs', 'saldo', 
            'aktifitas', 'broadcast', 'saldoserver', 'totaluser'], handleButton);
bot.action('back', (ctx) => handleStart(ctx));

bot.launch();

// Enable graceful stop
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
