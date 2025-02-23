from telethon import TelegramClient, events
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.types import User, Channel, Chat
from telethon.errors import (
    ChatWriteForbiddenError,
    UserIsBlockedError,
    MessageTooLongError,
    ChatAdminRequiredError,
    UserBannedInChannelError,
    FloodWaitError
)
import asyncio
import json
import logging
from datetime import datetime
import os
import sys
import traceback

# Configure logging with custom format
logging.basicConfig(
    format='%(asctime)s - 【%(levelname)s】 %(message)s',
    level=logging.INFO,
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Device Configuration
DEVICE_MODEL = "iPhone 16 Pro Max"
SYSTEM_VERSION = "17.4.1"
LANG_CODE = "id"
SYSTEM_LANG_CODE = "id"
APP_VERSION = "9.6.3"

# Replace these with your own values
API_ID = '29410328'
API_HASH = 'd7ce7094b2439df3c18d6b3197f5322a'

# Custom text styles
class TextStyle:
    # Emoji constants
    SUCCESS = "✨"
    ERROR = "❌"
    INFO = "ℹ️"
    WARNING = "⚠️"
    ROCKET = "🚀"
    CLOCK = "⏰"
    STAR = "⭐"
    
    @staticmethod
    def success(text):
        return f"{TextStyle.SUCCESS} 【 sᴜᴄᴄᴇss 】» {text}"
    
    @staticmethod
    def error(text):
        return f"{TextStyle.ERROR} 【 ᴇʀʀᴏʀ 】» {text}"
    
    @staticmethod
    def info(text):
        return f"{TextStyle.INFO} 【 ɪɴғᴏ 】» {text}"
    
    @staticmethod
    def warning(text):
        return f"{TextStyle.WARNING} 【 ᴡᴀʀɴɪɴɢ 】» {text}"
    
    @staticmethod
    def progress(current, total):
        percentage = (current / total) * 100
        return f"""
╭─────────────────────╮
├ 𝙿𝚛𝚘𝚐𝚛𝚎𝚜𝚜: {current}/{total}
├ 𝙿𝚎𝚛𝚌𝚎𝚗𝚝𝚊𝚐𝚎: {percentage:.1f}%
╰─────────────────────╯"""

# Initialize client with device info
client = TelegramClient(
    'iphone16promax_session',
    API_ID,
    API_HASH,
    device_model=DEVICE_MODEL,
    system_version=SYSTEM_VERSION,
    app_version=APP_VERSION,
    lang_code=LANG_CODE,
    system_lang_code=SYSTEM_LANG_CODE
)

# Store active tasks and blacklist
active_tasks = set()
blacklist = set()

def load_blacklist():
    try:
        with open('blacklist.json', 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()
    except Exception as e:
        logger.error(f"Failed to load blacklist: {e}")
        return set()

def save_blacklist():
    try:
        with open('blacklist.json', 'w') as f:
            json.dump(list(blacklist), f)
    except Exception as e:
        logger.error(f"Failed to save blacklist: {e}")

async def get_all_chats(target_type):
    all_chats = []
    try:
        async for dialog in client.iter_dialogs():
            if target_type == 'private' and isinstance(dialog.entity, User):
                all_chats.append(dialog)
            elif target_type == 'group' and (isinstance(dialog.entity, Channel) or isinstance(dialog.entity, Chat)):
                all_chats.append(dialog)
    except Exception as e:
        logger.error(f"Error getting chats: {e}")
    return all_chats

async def handle_forward_error(error, chat_name):
    error_msg = ""
    if isinstance(error, ChatWriteForbiddenError):
        error_msg = f"Cannot send messages to {chat_name}"
    elif isinstance(error, UserIsBlockedError):
        error_msg = f"User {chat_name} has blocked the bot"
    elif isinstance(error, MessageTooLongError):
        error_msg = "Message too long"
    elif isinstance(error, ChatAdminRequiredError):
        error_msg = f"Admin permissions required in {chat_name}"
    elif isinstance(error, UserBannedInChannelError):
        error_msg = f"Banned from sending to {chat_name}"
    elif isinstance(error, FloodWaitError):
        error_msg = f"Flood wait for {error.seconds} seconds"
        await asyncio.sleep(error.seconds)
    else:
        error_msg = str(error)
    return error_msg

@client.on(events.NewMessage(pattern=r'\.cfd (private|group)'))
async def continuous_forward(event):
    try:
        if not event.is_reply:
            await event.reply(TextStyle.warning("ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ!"))
            return

        target_type = event.pattern_match.group(1)
        message = await event.get_reply_message()
        
        task = asyncio.create_task(forward_to_all(event, message, target_type))
        active_tasks.add(task)
        task.add_done_callback(lambda t: active_tasks.remove(t))

        await event.reply(TextStyle.info(f"sᴛᴀʀᴛɪɴɢ ғᴏʀᴡᴀʀᴅ ᴛᴏ ᴀʟʟ {target_type}s..."))
    
    except Exception as e:
        error_msg = f"Error in continuous_forward: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        await event.reply(TextStyle.error(str(e)))

async def forward_to_all(event, message, target_type):
    success = 0
    failed = 0
    errors = {}
    
    try:
        all_chats = await get_all_chats(target_type)
        total_chats = len(all_chats)
        
        status_msg = await event.reply(TextStyle.info("ɪɴɪᴛɪᴀʟɪᴢɪɴɢ ғᴏʀᴡᴀʀᴅ..."))
        
        for i, dialog in enumerate(all_chats, 1):
            if dialog.id in blacklist:
                continue
                
            try:
                await client.forward_messages(dialog.id, message)
                success += 1
                logger.info(TextStyle.success(f"ғᴏʀᴡᴀʀᴅᴇᴅ ᴛᴏ {dialog.name}"))
            except Exception as e:
                failed += 1
                error_msg = await handle_forward_error(e, dialog.name)
                errors[dialog.name] = error_msg
                logger.error(TextStyle.error(f"ғᴀɪʟᴇᴅ ᴛᴏ ғᴏʀᴡᴀʀᴅ ᴛᴏ {dialog.name}: {error_msg}"))
            
            if i % 5 == 0:
                progress_text = TextStyle.progress(i, total_chats)
                status_text = f"""
{progress_text}
✨ sᴜᴄᴄᴇss: {success}
❌ ғᴀɪʟᴇᴅ: {failed}
⏳ ʀᴇᴍᴀɪɴɪɴɢ: {total_chats - i}"""
                await status_msg.edit(status_text)
        
        # Final status with error details
        final_status = f"""
╭──『 ғᴏʀᴡᴀʀᴅ ᴄᴏᴍᴘʟᴇᴛᴇ 』──╮
├ ✨ sᴜᴄᴄᴇss: {success}
├ ❌ ғᴀɪʟᴇᴅ: {failed}
├ 💫 ᴛᴏᴛᴀʟ: {total_chats}
╰────────────────────╯"""
        
        if errors:
            error_details = "\n".join(f"- {name}: {error}" for name, error in errors.items())
            final_status += f"\n\n❌ Error Details:\n{error_details}"
        
        await status_msg.edit(final_status)
        
    except Exception as e:
        error_msg = f"Error in forward_to_all: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        await event.reply(TextStyle.error(str(e)))

@client.on(events.NewMessage(pattern=r'\.forward (private|group)'))
async def continuous_forward_with_delay(event):
    try:
        if not event.is_reply:
            await event.reply(TextStyle.warning("ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ!"))
            return

        target_type = event.pattern_match.group(1)
        message = await event.get_reply_message()
        
        await event.reply(TextStyle.info("ᴇɴᴛᴇʀ ᴅᴇʟᴀʏ ɪɴ sᴇᴄᴏɴᴅs:"))
        
        try:
            response = await client.wait_for_message(
                from_users=[event.sender_id],
                timeout=30
            )
            delay = float(response.text)
        except asyncio.TimeoutError:
            await event.reply(TextStyle.warning("ɴᴏ ʀᴇsᴘᴏɴsᴇ ʀᴇᴄᴇɪᴠᴇᴅ. ᴄᴀɴᴄᴇʟʟɪɴɢ."))
            return
        except ValueError:
            await event.reply(TextStyle.warning("ɪɴᴠᴀʟɪᴅ ᴅᴇʟᴀʏ ᴠᴀʟᴜᴇ!"))
            return

        task = asyncio.create_task(continuous_forward_with_delay_task(event, message, target_type, delay))
        active_tasks.add(task)
        task.add_done_callback(lambda t: active_tasks.remove(t))

        await event.reply(TextStyle.info(f"sᴛᴀʀᴛɪɴɢ ᴄᴏɴᴛɪɴᴜᴏᴜs ғᴏʀᴡᴀʀᴅ ᴡɪᴛʜ {delay}s ᴅᴇʟᴀʏ..."))
    
    except Exception as e:
        error_msg = f"Error in continuous_forward_with_delay: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        await event.reply(TextStyle.error(str(e)))

async def continuous_forward_with_delay_task(event, message, target_type, delay):
    cycle = 1
    while True:
        try:
            success = 0
            failed = 0
            errors = {}
            
            all_chats = await get_all_chats(target_type)
            total_chats = len(all_chats)
            
            status_msg = await event.reply(f"""
╭──『 ᴄʏᴄʟᴇ #{cycle} 』──╮
├ 📊 sᴛᴀᴛᴜs: sᴛᴀʀᴛɪɴɢ
├ 🎯 ᴛᴀʀɢᴇᴛs: {total_chats}
╰────────────────╯""")
            
            for i, dialog in enumerate(all_chats, 1):
                if dialog.id in blacklist:
                    continue
                    
                try:
                    await client.forward_messages(dialog.id, message)
                    success += 1
                except Exception as e:
                    failed += 1
                    error_msg = await handle_forward_error(e, dialog.name)
                    errors[dialog.name] = error_msg
                
                if i % 5 == 0:
                    progress_text = TextStyle.progress(i, total_chats)
                    status_text = f"""
╭──『 ᴄʏᴄʟᴇ #{cycle} 』──╮
{progress_text}
├ ✨ sᴜᴄᴄᴇss: {success}
├ ❌ ғᴀɪʟᴇᴅ: {failed}
╰────────────────╯"""
                    await status_msg.edit(status_text)
            
            cycle_status = f"""
╭──『 ᴄʏᴄʟᴇ #{cycle} ᴄᴏᴍᴘʟᴇᴛᴇ 』──╮
├ ✨ sᴜᴄᴄᴇss: {success}
├ ❌ ғᴀɪʟᴇᴅ: {failed}
├ 💫 ᴛᴏᴛᴀʟ: {total_chats}
├ ⏳ ɴᴇxᴛ ᴄʏᴄʟᴇ ɪɴ: {delay}s
╰─────────────────────╯"""
            
            if errors:
                error_details = "\n".join(f"- {name}: {error}" for name, error in errors.items())
                cycle_status += f"\n\n❌ Error Details:\n{error_details}"
            
            await status_msg.edit(cycle_status)
            cycle += 1
            
            await asyncio.sleep(delay)
            
        except Exception as e:
            error_msg = f"Error in cycle {cycle}: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            await event.reply(TextStyle.error(f"ᴇʀʀᴏʀ ɪɴ ᴄʏᴄʟᴇ {cycle}: {str(e)}"))
            await asyncio.sleep(delay)  # Still wait before next cycle

@client.on(events.NewMessage(pattern=r'\.stop'))
async def stop_tasks(event):
    try:
        if not active_tasks:
            await event.reply(TextStyle.warning("ɴᴏ ᴀᴄᴛɪᴠᴇ ᴛᴀsᴋs!"))
            return
            
        for task in active_tasks.copy():
            task.cancel()
        
        await event.reply(TextStyle.success("ᴀʟʟ ᴛᴀsᴋs sᴛᴏᴘᴘᴇᴅ!"))
    
    except Exception as e:
        error_msg = f"Error in stop_tasks: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        await event.reply(TextStyle.error(str(e)))

@client.on(events.NewMessage(pattern=r'\.bl'))
async def add_to_blacklist(event):
    try:
        if event.is_private:
            blacklist.add(event.chat_id)
            await event.reply(TextStyle.success("ᴜsᴇʀ ᴀᴅᴅᴇᴅ ᴛᴏ ʙʟᴀᴄᴋʟɪsᴛ!"))
        else:
            blacklist.add(event.chat_id)
            await event.reply(TextStyle.success("ɢʀᴏᴜᴘ ᴀᴅᴅᴇᴅ ᴛᴏ ʙʟᴀᴄᴋʟɪsᴛ!"))
        
        save_blacklist()
    
    except Exception as e:
        error_msg = f"Error in add_to_blacklist: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        await event.reply(TextStyle.error(str(e)))

async def main():
    try:
        global blacklist
        blacklist = load_blacklist()
        
        print(TextStyle.info("sᴛᴀʀᴛɪɴɢ ᴜsᴇʀʙᴏᴛ..."))
        await client.start()
        
        welcome_msg = f"""
╭──『 ᴜsᴇʀʙᴏᴛ sᴛᴀʀᴛᴇᴅ 』──╮
├ 📱 ᴅᴇᴠɪᴄᴇ: {DEVICE_MODEL}
├ 📍 ʟᴏᴄᴀᴛɪᴏɴ: ɪɴᴅᴏɴᴇsɪᴀ
├ ⚡ sᴛᴀᴛᴜs: ᴏɴʟɪɴᴇ
╰─────────────────────╯"""
        print(welcome_msg)
        
        await client.run_until_disconnected()
    
    except Exception as e:
        error_msg = f"Error in main: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        sys.exit(1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(TextStyle.warning("\nᴜsᴇʀʙᴏᴛ sᴛᴏᴘᴘᴇᴅ ʙʏ ᴜsᴇʀ"))
    except Exception as e:
        print(TextStyle.error(f"ᴄʀɪᴛɪᴄᴀʟ ᴇʀʀᴏʀ: {str(e)}"))
