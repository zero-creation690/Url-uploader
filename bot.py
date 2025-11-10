import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.enums import ParseMode
from config import Config
from database import db
from downloader import downloader
from helpers import Progress, humanbytes, is_url
import time

# Initialize bot
app = Client(
    "url_uploader_bot",
    api_id=Config.APP_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# User settings and tasks storage
user_settings = {}
user_tasks = {}

# Start command with inline menu
@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    await db.add_user(user_id, username, first_name)
    
    text = f"""👋 Hi {first_name}!

I'm **URL Uploader X bot**. Just send me any Direct download link and I'll upload file remotely to Telegram.

**Supported:**
• Direct HTTP/HTTPS links
• YouTube, Instagram, TikTok videos
• Torrent files and magnet links
• Files up to 4GB

**Developer:** {Config.DEVELOPER}
**Updates:** {Config.UPDATE_CHANNEL}"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚙️ Go to Settings", callback_data="settings")],
        [InlineKeyboardButton("📊 Plan details", callback_data="plan"),
         InlineKeyboardButton("❓ Help", callback_data="help")]
    ])
    
    await message.reply_text(text, reply_markup=keyboard)

# Settings menu
@app.on_callback_query(filters.regex("^settings$"))
async def settings_menu(client, callback: CallbackQuery):
    user_id = callback.from_user.id
    settings = user_settings.get(user_id, {})
    
    text = "⚙️ **Here you can change bot settings**"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼️ Set thumbnail", callback_data="set_thumb")],
        [InlineKeyboardButton("📝 Set default caption", callback_data="set_caption")],
        [InlineKeyboardButton("✏️ Show rename option: ON", callback_data="rename_toggle")],
        [InlineKeyboardButton("📁 Upload as Document: OFF", callback_data="doc_toggle")],
        [InlineKeyboardButton("🎥 Upload as Video: ON", callback_data="video_toggle")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_start")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)

# Plan details
@app.on_callback_query(filters.regex("^plan$"))
async def plan_details(client, callback: CallbackQuery):
    text = """⏳ **Plan details**

**Current Plan:** Free Plan
**Max file size:** 4 GB
**Download speed:** 200 MB/s
**Torrent support:** ✅ Enabled
**Auto-rename:** ✅ Enabled

**Features:**
✅ Direct download links
✅ YouTube, Instagram downloads
✅ Torrent & magnet links
✅ Custom thumbnails
✅ Custom captions
✅ Batch downloads"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="back_start")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)

# Help menu
@app.on_callback_query(filters.regex("^help$"))
async def help_menu(client, callback: CallbackQuery):
    text = """📚 **Help me to learn bot**

**How to use:**
1️⃣ Send any URL, torrent file or magnet link
2️⃣ Bot will download it
3️⃣ Choose upload type (Document/Video)
4️⃣ Rename if needed
5️⃣ File uploaded!

**Commands:**
/start - Start bot
/rename - Rename file
/set_caption - Set caption
/set_thumb - Set thumbnail
/delete_thumb - Delete thumbnail

**Supported links:**
• Direct downloads (HTTP/HTTPS)
• YouTube videos
• Instagram posts/reels
• TikTok videos
• Torrent files (.torrent)
• Magnet links

**Speed:** 200 MB/s blazing fast! 🚀"""
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back", callback_data="back_start")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)

# Back to start
@app.on_callback_query(filters.regex("^back_start$"))
async def back_start(client, callback: CallbackQuery):
    await start_command(client, callback.message)

# Handle file upload type selection
@app.on_callback_query(filters.regex("^upload_"))
async def handle_upload_type(client, callback: CallbackQuery):
    data = callback.data
    user_id = callback.from_user.id
    
    if user_id not in user_tasks:
        await callback.answer("Task expired! Send URL again.", show_alert=True)
        return
    
    task = user_tasks[user_id]
    filepath = task['filepath']
    upload_type = data.split('_')[1]  # doc or video
    
    await callback.message.edit_text("⬆️ **Uploading to Telegram...**")
    
    try:
        # Get user settings
        settings = user_settings.get(user_id, {})
        thumbnail = settings.get('thumbnail')
        caption = settings.get('caption', f"📁 **File:** {os.path.basename(filepath)}\n💾 **Size:** {humanbytes(os.path.getsize(filepath))}\n\n**Uploaded by:** {Config.DEVELOPER}")
        
        # Progress tracker
        progress = Progress(client, callback.message)
        
        if upload_type == 'doc':
            # Upload as document
            await client.send_document(
                chat_id=callback.message.chat.id,
                document=filepath,
                caption=caption,
                thumb=thumbnail,
                progress=progress.progress_callback,
                progress_args=("Uploading",)
            )
        else:
            # Upload as video
            await client.send_video(
                chat_id=callback.message.chat.id,
                video=filepath,
                caption=caption,
                thumb=thumbnail,
                supports_streaming=True,
                progress=progress.progress_callback,
                progress_args=("Uploading",)
            )
        
        # Update stats
        await db.update_stats(user_id, upload=True)
        await db.log_action(user_id, "upload", filepath)
        
        # Delete status message
        await callback.message.delete()
        
        # Send completion message
        await callback.message.reply_text(
            "✅ **Upload complete!**\n\nYou can send new task now",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
            ])
        )
        
    except Exception as e:
        await callback.message.edit_text(f"❌ **Upload failed:** {str(e)}")
    
    finally:
        # Cleanup
        downloader.cleanup(filepath)
        if user_id in user_tasks:
            del user_tasks[user_id]

# Handle rename
@app.on_callback_query(filters.regex("^rename_"))
async def handle_rename(client, callback: CallbackQuery):
    data = callback.data
    user_id = callback.from_user.id
    
    if data == "rename_now":
        await callback.message.edit_text(
            "📝 **Send new name for this file** - 📁 " + 
            os.path.basename(user_tasks[user_id]['filepath'])
        )
        user_tasks[user_id]['waiting_rename'] = True
    elif data == "rename_skip":
        # Show upload options
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📁 Upload as Document", callback_data="upload_doc")],
            [InlineKeyboardButton("🎥 Upload as Video", callback_data="upload_video")]
        ])
        await callback.message.edit_text(
            "**Choose upload type:**",
            reply_markup=keyboard
        )

# Main URL/Torrent handler
@app.on_message((filters.text | filters.document) & filters.private)
async def handle_download(client, message: Message):
    user_id = message.from_user.id
    
    # Check if it's a torrent file
    if message.document and message.document.file_name.endswith('.torrent'):
        torrent_path = await message.download()
        url = torrent_path
    elif message.text:
        url = message.text.strip()
        if not is_url(url) and not url.startswith('magnet:'):
            return
    else:
        return
    
    await db.add_user(user_id, message.from_user.username, message.from_user.first_name)
    
    # Initial message
    status_msg = await message.reply_text("🔄 **Processing your request...**")
    
    try:
        # Download file
        progress = Progress(client, status_msg)
        filepath, error = await downloader.download(url, progress_callback=progress.progress_callback)
        
        if error:
            await status_msg.edit_text(f"❌ **Error:** {error}")
            return
        
        # Update stats
        await db.update_stats(user_id, download=True)
        await db.log_action(user_id, "download", url)
        
        # Store task for user
        user_tasks[user_id] = {
            'filepath': filepath,
            'url': url if isinstance(url, str) else 'torrent'
        }
        
        # Ask for rename
        file_size = os.path.getsize(filepath) if os.path.isfile(filepath) else 0
        filename = os.path.basename(filepath)
        
        text = (
            f"✅ **Download Complete!**\n\n"
            f"📁 **File:** `{filename}`\n"
            f"💾 **Size:** {humanbytes(file_size)}\n\n"
            f"**Send new name for this file** - 📁 {filename}"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Rename now", callback_data="rename_now")],
            [InlineKeyboardButton("⏭️ Skip", callback_data="rename_skip")]
        ])
        
        await status_msg.edit_text(text, reply_markup=keyboard)
        
        # Log to channel
        try:
            await client.send_message(
                Config.LOG_CHANNEL,
                f"📥 **New Download**\n\n"
                f"**User:** {message.from_user.mention}\n"
                f"**File:** {filename}\n"
                f"**Size:** {humanbytes(file_size)}\n"
                f"**Source:** `{url if isinstance(url, str) else 'Torrent file'}`"
            )
        except Exception:
            pass
            
    except Exception as e:
        await status_msg.edit_text(f"❌ **Error:** {str(e)}")
        await db.log_action(user_id, "error", str(e))

# Handle rename input
@app.on_message(filters.text & filters.private)
async def handle_rename_input(client, message: Message):
    user_id = message.from_user.id
    
    if user_id in user_tasks and user_tasks[user_id].get('waiting_rename'):
        new_name = message.text.strip()
        filepath = user_tasks[user_id]['filepath']
        
        # Rename file
        new_path = os.path.join(os.path.dirname(filepath), new_name)
        os.rename(filepath, new_path)
        user_tasks[user_id]['filepath'] = new_path
        user_tasks[user_id]['waiting_rename'] = False
        
        # Show upload options
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📁 Upload as Document", callback_data="upload_doc")],
            [InlineKeyboardButton("🎥 Upload as Video", callback_data="upload_video")]
        ])
        
        await message.reply_text(
            f"✅ **Renamed to:** `{new_name}`\n\n**Choose upload type:**",
            reply_markup=keyboard
        )

# Handle thumbnail
@app.on_message(filters.photo & filters.private)
async def handle_thumbnail(client, message: Message):
    user_id = message.from_user.id
    
    thumb_path = await message.download(file_name=f"{Config.DOWNLOAD_DIR}/thumb_{user_id}.jpg")
    
    if user_id not in user_settings:
        user_settings[user_id] = {}
    user_settings[user_id]['thumbnail'] = thumb_path
    
    await message.reply_text("✅ **Thumbnail set successfully!**")

# Set caption command
@app.on_message(filters.command("set_caption"))
async def set_caption_cmd(client, message: Message):
    user_id = message.from_user.id
    
    if len(message.command) < 2:
        await message.reply_text("Usage: `/set_caption Your caption here`")
        return
    
    caption = message.text.split(None, 1)[1]
    
    if user_id not in user_settings:
        user_settings[user_id] = {}
    user_settings[user_id]['caption'] = caption
    
    await message.reply_text("✅ **Default caption set!**")

# Status command
@app.on_message(filters.command("status"))
async def status_command(client, message: Message):
    user_id = message.from_user.id
    user_data = await db.get_user(user_id)
    
    if user_data:
        text = (
            "📊 **Your Statistics**\n\n"
            f"**User ID:** `{user_id}`\n"
            f"**Username:** @{user_data.get('username', 'N/A')}\n"
            f"**Total Downloads:** {user_data.get('total_downloads', 0)}\n"
            f"**Total Uploads:** {user_data.get('total_uploads', 0)}\n"
            f"**Member since:** {user_data.get('joined_date').strftime('%Y-%m-%d')}"
        )
    else:
        text = "No data found!"
    
    await message.reply_text(text)

# Broadcast command (owner only)
@app.on_message(filters.command("broadcast") & filters.user(Config.OWNER_ID))
async def broadcast_command(client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("Reply to a message to broadcast!")
        return
    
    users = await db.get_all_users()
    broadcast_msg = message.reply_to_message
    
    success = 0
    failed = 0
    
    status_msg = await message.reply_text("📢 Broadcasting...")
    
    for user in users:
        try:
            await broadcast_msg.copy(user['user_id'])
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
    
    await status_msg.edit_text(
        f"✅ **Broadcast Complete**\n\n"
        f"Success: {success}\n"
        f"Failed: {failed}"
    )

# Run bot
if __name__ == "__main__":
    print("🚀 URL Uploader X Bot starting...")
    print(f"👨‍💻 Developer: {Config.DEVELOPER}")
    print(f"📢 Updates: {Config.UPDATE_CHANNEL}")
    app.run()
