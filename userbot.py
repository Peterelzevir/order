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
from datetime import datetime, timedelta
import os
import sys
import traceback
import sqlite3
import pytz

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
APP_VERSION = "10.8.3"

# Replace these with your own values
API_ID = '29410328'
API_HASH = 'd7ce7094b2439df3c18d6b3197f5322a'
OWNER_ID = '5988451717'  # Ganti dengan ID Telegram owner/admin utama

# Get WIB timezone
WIB = pytz.timezone('Asia/Jakarta')

def get_wib_time():
    return datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")

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

# Database setup
def setup_database():
    conn = sqlite3.connect('userbot_admin.db')
    c = conn.cursor()
    
    # Create clone sessions table
    c.execute('''CREATE TABLE IF NOT EXISTS clone_sessions
                 (phone TEXT PRIMARY KEY, 
                  expiry_date TEXT,
                  password TEXT,
                  session_file TEXT,
                  is_active INTEGER,
                  clone_user_id TEXT)''')

    # Create admins table
    c.execute('''CREATE TABLE IF NOT EXISTS admins
                 (user_id TEXT PRIMARY KEY,
                  added_date TEXT)''')
                  
    # Add owner as default admin if table is empty
    c.execute('SELECT COUNT(*) FROM admins')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO admins VALUES (?, ?)', 
                 (OWNER_ID, datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()

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

# Clone session management
async def create_clone_session(phone, duration_days, password, session_file, clone_user_id):
    conn = sqlite3.connect('userbot_admin.db')
    c = conn.cursor()
    expiry_date = (datetime.now(WIB) + timedelta(days=duration_days)).strftime("%Y-%m-%d")
    
    c.execute('''INSERT OR REPLACE INTO clone_sessions 
                 (phone, expiry_date, password, session_file, is_active, clone_user_id)
                 VALUES (?, ?, ?, ?, 1, ?)''',
              (phone, expiry_date, password, session_file, clone_user_id))
    conn.commit()
    conn.close()

async def check_expired_sessions():
    while True:
        try:
            conn = sqlite3.connect('userbot_admin.db')
            c = conn.cursor()
            current_date = datetime.now(WIB).strftime("%Y-%m-%d")
            
            # Get expired sessions
            c.execute('''SELECT phone, session_file, clone_user_id FROM clone_sessions 
                        WHERE expiry_date < ? AND is_active = 1''', (current_date,))
            expired_sessions = c.fetchall()
            
            for phone, session_file, clone_user_id in expired_sessions:
                # Update session status
                c.execute('''UPDATE clone_sessions SET is_active = 0 
                           WHERE phone = ?''', (phone,))
                
                # Delete session file
                if os.path.exists(session_file):
                    os.remove(session_file)
                
                # Send notification to admin
                admin_msg = f"""
╭──『 SESSION EXPIRED 』──╮
├ 📱 Phone: {phone}
├ ⏰ Expired: {current_date}
├ 📍 Status: Deactivated
╰─────────────────────╯"""
                await client.send_message('me', TextStyle.warning(admin_msg))

                # Send notification to clone user
                if clone_user_id:
                    clone_msg = f"""
╭──『 USERBOT EXPIRED 』──╮
├ 📱 Phone: {phone}
├ ⏰ Expired Date: {current_date}
├ 📍 Status: Non-Active
├ ℹ️ Info: Session automatically deactivated
╰─────────────────────╯"""
                    try:
                        await client.send_message(int(clone_user_id), TextStyle.warning(clone_msg))
                    except Exception as e:
                        logger.error(f"Failed to send notification to clone user {clone_user_id}: {e}")
            
            conn.commit()
            conn.close()
            
            await asyncio.sleep(3600)  # Check every hour
            
        except Exception as e:
            logger.error(f"Error checking expired sessions: {e}")
            await asyncio.sleep(3600)

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

# Clone management functions
@client.on(events.NewMessage(pattern=r'\.userbots'))
async def list_userbots(event):
    try:
        if str(event.sender_id) != OWNER_ID:
            await event.reply(TextStyle.error("ᴏɴʟʏ ᴏᴡɴᴇʀ ᴄᴀɴ ᴠɪᴇᴡ ᴜsᴇʀʙᴏᴛ ʟɪsᴛ!"))
            return
            
        conn = sqlite3.connect('userbot_admin.db')
        c = conn.cursor()
        c.execute('''SELECT phone, expiry_date, clone_user_id, is_active 
                    FROM clone_sessions ORDER BY is_active DESC, expiry_date ASC''')
        userbots = c.fetchall()
        conn.close()
        
        if not userbots:
            await event.reply(TextStyle.warning("ɴᴏ ᴜsᴇʀʙᴏᴛs ғᴏᴜɴᴅ!"))
            return
            
        current_date = datetime.now(WIB).strftime("%Y-%m-%d")
        userbot_list = "╭──『 ᴜsᴇʀʙᴏᴛ ʟɪsᴛ 』──╮\n"
        
        for phone, expiry_date, user_id, is_active in userbots:
            status = "Active ✅" if is_active else "Non-Active ❌"
            remaining_days = (datetime.strptime(expiry_date, "%Y-%m-%d") - 
                            datetime.strptime(current_date, "%Y-%m-%d")).days
            
            userbot_list += f"├──────────\n"
            userbot_list += f"├ 📱 Phone: {phone}\n"
            userbot_list += f"├ 👤 User ID: {user_id}\n"
            userbot_list += f"├ ⏰ Expires: {expiry_date}\n"
            userbot_list += f"├ ⌛ Days Left: {remaining_days}\n"
            userbot_list += f"├ 📍 Status: {status}\n"
            
        userbot_list += "╰────────────────╯"
        
        await event.reply(userbot_list)
        
    except Exception as e:
        error_msg = f"Error in list_userbots: {str(e)}"
        logger.error(error_msg)
        await event.reply(TextStyle.error(str(e)))

@client.on(events.NewMessage(pattern=r'\.deluserbot'))
async def delete_userbot(event):
    try:
        if str(event.sender_id) != OWNER_ID:
            await event.reply(TextStyle.error("ᴏɴʟʏ ᴏᴡɴᴇʀ ᴄᴀɴ ᴅᴇʟᴇᴛᴇ ᴜsᴇʀʙᴏᴛs!"))
            return
            
        # Get phone number
        msg = await event.reply(TextStyle.info("Enter phone number of userbot to delete:"))
        try:
            response = await client.wait_for_message(
                from_users=[event.sender_id],
                timeout=30
            )
            phone = response.text.strip()
            await response.delete()
            await msg.delete()
        except asyncio.TimeoutError:
            await event.reply(TextStyle.error("No response received! Process cancelled."))
            return
            
        # Get userbot info
        conn = sqlite3.connect('userbot_admin.db')
        c = conn.cursor()
        c.execute('SELECT session_file, clone_user_id FROM clone_sessions WHERE phone = ?', (phone,))
        result = c.fetchone()
        
        if not result:
            await event.reply(TextStyle.error("ᴜsᴇʀʙᴏᴛ ɴᴏᴛ ғᴏᴜɴᴅ!"))
            conn.close()
            return
            
        session_file, clone_user_id = result
        
        # Delete session file
        if os.path.exists(session_file):
            os.remove(session_file)
            
        # Delete from database
        c.execute('DELETE FROM clone_sessions WHERE phone = ?', (phone,))
        conn.commit()
        conn.close()
        
        # Send notification to clone user
        delete_msg = f"""
╭──『 ᴜsᴇʀʙᴏᴛ ᴅᴇʟᴇᴛᴇᴅ 』──╮
├ 📱 Phone: {phone}
├ ℹ️ Status: Deleted by owner
├ ⏰ Time: {get_wib_time()}
╰─────────────────────╯"""
        
        try:
            await client.send_message(int(clone_user_id), TextStyle.warning(delete_msg))
        except Exception as e:
            logger.error(f"Failed to send notification to clone user {clone_user_id}: {e}")
        
        # Confirm to owner
        success_msg = f"""
╭──『 ᴜsᴇʀʙᴏᴛ ᴅᴇʟᴇᴛᴇᴅ 』──╮
├ 📱 Phone: {phone}
├ 👤 User ID: {clone_user_id}
├ 📍 Status: Deleted
├ ⏰ Time: {get_wib_time()}
╰─────────────────────╯"""
        await event.reply(TextStyle.success(success_msg))
        
    except Exception as e:
        error_msg = f"Error in delete_userbot: {str(e)}"
        logger.error(error_msg)
        await event.reply(TextStyle.error(str(e)))
    conn = sqlite3.connect('userbot_admin.db')
    c = conn.cursor()
    c.execute('SELECT * FROM admins WHERE user_id = ?', (str(user_id),))
    result = c.fetchone()
    conn.close()
    return bool(result)

@client.on(events.NewMessage(pattern=r'\.addadmin'))
async def add_admin(event):
    try:
        if str(event.sender_id) != OWNER_ID:
            await event.reply(TextStyle.error("ᴏɴʟʏ ᴏᴡɴᴇʀ ᴄᴀɴ ᴀᴅᴅ ᴀᴅᴍɪɴs!"))
            return
            
        if not event.is_reply:
            await event.reply(TextStyle.warning("ʀᴇᴘʟʏ ᴛᴏ ᴛʜᴇ ᴜsᴇʀ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴀᴅᴅ ᴀs ᴀᴅᴍɪɴ!"))
            return
            
        replied = await event.get_reply_message()
        new_admin_id = str(replied.sender_id)
        
        if await is_admin(new_admin_id):
            await event.reply(TextStyle.warning("ᴜsᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ᴀɴ ᴀᴅᴍɪɴ!"))
            return
            
        conn = sqlite3.connect('userbot_admin.db')
        c = conn.cursor()
        c.execute('INSERT INTO admins VALUES (?, ?)',
                 (new_admin_id, datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        
        await event.reply(TextStyle.success("ɴᴇᴡ ᴀᴅᴍɪɴ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!"))
        
    except Exception as e:
        error_msg = f"Error in add_admin: {str(e)}"
        logger.error(error_msg)
        await event.reply(TextStyle.error(str(e)))

@client.on(events.NewMessage(pattern=r'\.rmadmin'))
async def remove_admin(event):
    try:
        if str(event.sender_id) != OWNER_ID:
            await event.reply(TextStyle.error("ᴏɴʟʏ ᴏᴡɴᴇʀ ᴄᴀɴ ʀᴇᴍᴏᴠᴇ ᴀᴅᴍɪɴs!"))
            return
            
        if not event.is_reply:
            await event.reply(TextStyle.warning("ʀᴇᴘʟʏ ᴛᴏ ᴛʜᴇ ᴀᴅᴍɪɴ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ʀᴇᴍᴏᴠᴇ!"))
            return
            
        replied = await event.get_reply_message()
        admin_id = str(replied.sender_id)
        
        if admin_id == OWNER_ID:
            await event.reply(TextStyle.error("ᴄᴀɴɴᴏᴛ ʀᴇᴍᴏᴠᴇ ᴏᴡɴᴇʀ!"))
            return
            
        if not await is_admin(admin_id):
            await event.reply(TextStyle.warning("ᴜsᴇʀ ɪs ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ!"))
            return
            
        conn = sqlite3.connect('userbot_admin.db')
        c = conn.cursor()
        c.execute('DELETE FROM admins WHERE user_id = ?', (admin_id,))
        conn.commit()
        conn.close()
        
        await event.reply(TextStyle.success("ᴀᴅᴍɪɴ ʀᴇᴍᴏᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!"))
        
    except Exception as e:
        error_msg = f"Error in remove_admin: {str(e)}"
        logger.error(error_msg)
        await event.reply(TextStyle.error(str(e)))

@client.on(events.NewMessage(pattern=r'\.admins'))
async def list_admins(event):
    try:
        if not await is_admin(event.sender_id):
            await event.reply(TextStyle.error("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ!"))
            return
            
        conn = sqlite3.connect('userbot_admin.db')
        c = conn.cursor()
        c.execute('SELECT * FROM admins')
        admins = c.fetchall()
        conn.close()
        
        if not admins:
            await event.reply(TextStyle.warning("ɴᴏ ᴀᴅᴍɪɴs ғᴏᴜɴᴅ!"))
            return
            
        admin_list = "╭──『 ᴀᴅᴍɪɴ ʟɪsᴛ 』──╮\n"
        for admin_id, added_date in admins:
            admin_list += f"├ 👤 ID: {admin_id}\n"
            admin_list += f"├ 📅 Added: {added_date}\n"
            if admin_id == OWNER_ID:
                admin_list += "├ 👑 Owner\n"
            admin_list += "├──────────\n"
        admin_list += "╰────────────────╯"
        
        await event.reply(admin_list)
        
    except Exception as e:
        error_msg = f"Error in list_admins: {str(e)}"
        logger.error(error_msg)
        await event.reply(TextStyle.error(str(e)))

@client.on(events.NewMessage(pattern=r'\.clone'))
async def clone_command(event):
    if not event.is_private:
        return
        
    try:
        if not await is_admin(event.sender_id):
            await event.reply(TextStyle.error("ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ!"))
            return
        
    try:
        # Initial message
        msg = await event.reply(TextStyle.info("Enter duration (in days):"))
        
        # Get duration
        try:
            response = await client.wait_for_message(
                from_users=[event.sender_id],
                timeout=30
            )
            duration = int(response.text)
            await response.delete()
            await msg.delete()
        except (asyncio.TimeoutError, ValueError):
            await event.reply(TextStyle.error("Invalid duration! Process cancelled."))
            return
            
        # Get phone number
        msg = await event.reply(TextStyle.info("Enter phone number:"))
        try:
            response = await client.wait_for_message(
                from_users=[event.sender_id],
                timeout=30
            )
            phone = response.text
            await response.delete()
            await msg.delete()
        except asyncio.TimeoutError:
            await event.reply(TextStyle.error("No response received! Process cancelled."))
            return
            
        # Get OTP
        msg = await event.reply(TextStyle.info("Enter OTP:"))
        try:
            response = await client.wait_for_message(
                from_users=[event.sender_id],
                timeout=30
            )
            otp = response.text
            await response.delete()
            await msg.delete()
        except asyncio.TimeoutError:
            await event.reply(TextStyle.error("No OTP received! Process cancelled."))
            return
            
        # Get 2FA password if needed
        msg = await event.reply(TextStyle.info("Enter 2FA password (or 'skip' if none):"))
        try:
            response = await client.wait_for_message(
                from_users=[event.sender_id],
                timeout=30
            )
            password = None if response.text.lower() == 'skip' else response.text
            await response.delete()
            await msg.delete()
        except asyncio.TimeoutError:
            await event.reply(TextStyle.error("No response received! Process cancelled."))
            return
            
        # Get clone user ID
        msg = await event.reply(TextStyle.info("Enter clone user ID:"))
        try:
            response = await client.wait_for_message(
                from_users=[event.sender_id],
                timeout=30
            )
            clone_user_id = response.text
            await response.delete()
            await msg.delete()
        except asyncio.TimeoutError:
            await event.reply(TextStyle.error("No user ID received! Process cancelled."))
            return
            
        # Create session
        session_file = f"clone_{phone}_session"
        await create_clone_session(phone, duration, password, session_file, clone_user_id)
        
        success_msg = f"""
╭──『 CLONE SUCCESS 』──╮
├ 📱 Phone: {phone}
├ ⏰ Duration: {duration} days
├ 👤 User ID: {clone_user_id}
├ 📍 Created: {get_wib_time()}
╰─────────────────────╯"""
        await event.reply(TextStyle.success(success_msg))
        
        # Send notification to clone user
        clone_msg = f"""
╭──『 USERBOT ACTIVATED 』──╮
├ 📱 Phone: {phone}
├ ⏰ Duration: {duration} days
├ 📍 Expiry: {(datetime.now(WIB) + timedelta(days=duration)).strftime("%Y-%m-%d")}
├ ℹ️ Status: Active
╰─────────────────────╯"""
        try:
            await client.send_message(int(clone_user_id), TextStyle.success(clone_msg))
        except Exception as e:
            logger.error(f"Failed to send notification to clone user {clone_user_id}: {e}")
        
    except Exception as e:
        error_msg = f"Error in clone process: {str(e)}"
        logger.error(error_msg)
        await event.reply(TextStyle.error(error_msg))

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
        # Check and setup owner if needed
        if not OWNER_ID:
            await setup_owner()
            return
            
        # Setup database
        if not setup_database():
            return
        
        # Start expired session checker
        asyncio.create_task(check_expired_sessions())
        
        global blacklist
        blacklist = load_blacklist()
        
        print(TextStyle.info("sᴛᴀʀᴛɪɴɢ ᴜsᴇʀʙᴏᴛ..."))
        await client.start()
        
        welcome_msg = f"""
╭──『 ᴜsᴇʀʙᴏᴛ sᴛᴀʀᴛᴇᴅ 』──╮
├ 📱 ᴅᴇᴠɪᴄᴇ: {DEVICE_MODEL}
├ 📍 ʟᴏᴄᴀᴛɪᴏɴ: ɪɴᴅᴏɴᴇsɪᴀ
├ ⚡ sᴛᴀᴛᴜs: ᴏɴʟɪɴᴇ
├ 👑 ᴏᴡɴᴇʀ: {OWNER_ID}
├ ⏰ ᴛɪᴍᴇ: {get_wib_time()}
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
