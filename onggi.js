const TelegramBot = require('node-telegram-bot-api');
const sharp = require('sharp');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Ganti dengan token bot Telegram Anda
const token = '7779162915:AAG9k8jeoQO3q1whG9RRh2rDhZ_ouBH4weU';
const bot = new TelegramBot(token, { polling: true });

// Buat folder untuk menyimpan file sementara
const tempDir = path.join(__dirname, 'temp');
if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir);
}

// Animasi loading
const loadingFrames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
let loadingInterval;

// Fungsi untuk menampilkan animasi loading
async function showLoading(chatId, initialText) {
    let frame = 0;
    const message = await bot.sendMessage(chatId, `${loadingFrames[0]} ${initialText}`);
    
    loadingInterval = setInterval(async () => {
        frame = (frame + 1) % loadingFrames.length;
        try {
            await bot.editMessageText(
                `${loadingFrames[frame]} ${initialText}`,
                {
                    chat_id: chatId,
                    message_id: message.message_id
                }
            );
        } catch (error) {
            console.log('Error updating loading animation:', error);
        }
    }, 500);

    return message;
}

// Fungsi untuk menghentikan animasi loading
function stopLoading() {
    if (loadingInterval) {
        clearInterval(loadingInterval);
    }
}

// Handle pesan foto
bot.on('photo', async (msg) => {
    const chatId = msg.chat.id;
    let loadingMessage;
    
    try {
        loadingMessage = await showLoading(chatId, 'Sedang mengkonversi foto ke sticker...');
        
        const photo = msg.photo[msg.photo.length - 1];
        const file = await bot.getFile(photo.file_id);
        const photoUrl = `https://api.telegram.org/file/bot${token}/${file.file_path}`;
        
        // Update status
        await bot.editMessageText(
            '📥 Downloading foto...',
            {
                chat_id: chatId,
                message_id: loadingMessage.message_id,
                parse_mode: 'HTML'
            }
        );

        const response = await axios({
            url: photoUrl,
            method: 'GET',
            responseType: 'arraybuffer'
        });

        const photoPath = path.join(tempDir, `${photo.file_id}.png`);
        fs.writeFileSync(photoPath, response.data);

        // Update status
        await bot.editMessageText(
            '🎨 Processing image...',
            {
                chat_id: chatId,
                message_id: loadingMessage.message_id
            }
        );

        const stickerPath = path.join(tempDir, `${photo.file_id}.webp`);
        await sharp(photoPath)
            .resize(512, 512, {
                fit: 'contain',
                background: { r: 0, g: 0, b: 0, alpha: 0 }
            })
            .toFormat('webp')
            .toFile(stickerPath);

        // Update status
        await bot.editMessageText(
            '📤 Sending sticker...',
            {
                chat_id: chatId,
                message_id: loadingMessage.message_id
            }
        );

        await bot.sendSticker(chatId, stickerPath);
        
        // Success message dengan formatting
        await bot.editMessageText(
            '✅ *Konversi Berhasil\\!*\n\n' +
            '📸 Foto → 🎭 Sticker\n' +
            '_Processed in: ' + ((Date.now() - msg.date * 1000) / 1000).toFixed(2) + ' seconds_',
            {
                chat_id: chatId,
                message_id: loadingMessage.message_id,
                parse_mode: 'MarkdownV2'
            }
        );

        // Cleanup
        fs.unlinkSync(photoPath);
        fs.unlinkSync(stickerPath);

    } catch (error) {
        console.error('Error:', error);
        if (loadingMessage) {
            await bot.editMessageText(
                '❌ *Error\\!*\n_Gagal mengkonversi foto ke sticker\\. Silakan coba lagi\\._',
                {
                    chat_id: chatId,
                    message_id: loadingMessage.message_id,
                    parse_mode: 'MarkdownV2'
                }
            );
        }
    } finally {
        stopLoading();
    }
});

// Handle pesan sticker
bot.on('sticker', async (msg) => {
    const chatId = msg.chat.id;
    let loadingMessage;
    
    try {
        loadingMessage = await showLoading(chatId, 'Sedang mengkonversi sticker ke foto...');
        
        const sticker = msg.sticker;
        const file = await bot.getFile(sticker.file_id);
        const stickerUrl = `https://api.telegram.org/file/bot${token}/${file.file_path}`;
        
        // Update status
        await bot.editMessageText(
            '📥 Downloading sticker...',
            {
                chat_id: chatId,
                message_id: loadingMessage.message_id
            }
        );

        const response = await axios({
            url: stickerUrl,
            method: 'GET',
            responseType: 'arraybuffer'
        });

        const stickerPath = path.join(tempDir, `${sticker.file_id}.webp`);
        fs.writeFileSync(stickerPath, response.data);

        // Update status
        await bot.editMessageText(
            '🎨 Processing sticker...',
            {
                chat_id: chatId,
                message_id: loadingMessage.message_id
            }
        );

        const photoPath = path.join(tempDir, `${sticker.file_id}.png`);
        await sharp(stickerPath)
            .toFormat('png')
            .toFile(photoPath);

        // Update status
        await bot.editMessageText(
            '📤 Sending photo...',
            {
                chat_id: chatId,
                message_id: loadingMessage.message_id
            }
        );

        await bot.sendPhoto(chatId, photoPath);
        
        // Success message dengan formatting
        await bot.editMessageText(
            '✅ *Konversi Berhasil\\!*\n\n' +
            '🎭 Sticker → 📸 Foto\n' +
            '_Processed in: ' + ((Date.now() - msg.date * 1000) / 1000).toFixed(2) + ' seconds_',
            {
                chat_id: chatId,
                message_id: loadingMessage.message_id,
                parse_mode: 'MarkdownV2'
            }
        );

        // Cleanup
        fs.unlinkSync(stickerPath);
        fs.unlinkSync(photoPath);

    } catch (error) {
        console.error('Error:', error);
        if (loadingMessage) {
            await bot.editMessageText(
                '❌ *Error\\!*\n_Gagal mengkonversi sticker ke foto\\. Silakan coba lagi\\._',
                {
                    chat_id: chatId,
                    message_id: loadingMessage.message_id,
                    parse_mode: 'MarkdownV2'
                }
            );
        }
    } finally {
        stopLoading();
    }
});

// Handle command /start
bot.onText(/\/start/, async (msg) => {
    const chatId = msg.chat.id;
    const firstName = msg.from.first_name;
    
    const welcomeMessage = 
        '🎨 *Welcome to Sticker Converter Bot\\!*\n\n' +
        `Hello ${firstName}\\! Saya akan membantu Anda mengkonversi:\\!\n\n` +
        '1\\. 📸 *Foto ke Sticker*\n' +
        '2\\. 🎭 *Sticker ke Foto*\n\n' +
        '_Cara Penggunaan:_\n' +
        '• Kirim foto untuk dikonversi ke sticker\n' +
        '• Kirim sticker untuk dikonversi ke foto\n\n' +
        '💡 *Tips:*\n' +
        '• Foto akan di\\-resize menjadi 512x512\n' +
        '• Hasil terbaik menggunakan foto dengan rasio 1:1\n\n' +
        '_Bot akan otomatis mendeteksi dan mengkonversi\\!_';

    await bot.sendMessage(chatId, welcomeMessage, {
        parse_mode: 'MarkdownV2'
    });
});

// Handle command /help
bot.onText(/\/help/, async (msg) => {
    const chatId = msg.chat.id;
    
    const helpMessage = 
        '❓ *Bantuan Penggunaan Bot*\n\n' +
        '*Perintah yang tersedia:*\n' +
        '• /start \\- Memulai bot\n' +
        '• /help \\- Menampilkan bantuan\n\n' +
        '*Fitur:*\n' +
        '• Konversi foto ke sticker\n' +
        '• Konversi sticker ke foto\n' +
        '• Progress realtime\n' +
        '• Support semua format foto\n\n' +
        '*Ada masalah?*\n' +
        'Hubungi: @YourUsername';

    await bot.sendMessage(chatId, helpMessage, {
        parse_mode: 'MarkdownV2'
    });
});

console.log('🚀 Bot telah aktif!');
