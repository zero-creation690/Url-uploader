import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram API credentials
    APP_ID = int(os.environ.get("APP_ID", "20288994"))
    API_HASH = os.environ.get("API_HASH", "d702614912f1ad370a0d18786002adbf")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8062010233:AAExAW3Z-kpT17OTUXg0GQkCVsc7qnDUbXQ")
    BOT_USERNAME = os.environ.get("BOT_USERNAME", "@Urluploader_z_bot")
    
    # Database
    DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb+srv://moviedatabase:venura%408907@cluster0.hg0etvt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    
    # Logging
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1002897456594"))
    
    # Owner
    OWNER_ID = int(os.environ.get("OWNER_ID", "8304706556"))
    
    # Session for user bot (if needed)
    SESSION_STR = os.environ.get("SESSION_STR", "")
    
    # Update channel
    UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "https://t.me/zerodevbro")
    DEVELOPER = "@Zeroboy216"
    
    # Download/Upload settings
    MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4 GB
    SPEED_LIMIT = 500 * 1024 * 1024  # 500 MB/s (SUPER FAST!)
    CHUNK_SIZE = 2 * 1024 * 1024  # 2 MB chunks for maximum speed
    
    # Download directory
    DOWNLOAD_DIR = "downloads"
    
    # Torrent settings
    TORRENT_DOWNLOAD_PATH = "downloads/torrents"
    TORRENT_SEED_TIME = 0  # Don't seed after download
    
    # Welcome message
    START_MESSAGE = """👋 **Hi {name}!**

🎬 **I'm URL Uploader bot**. Just send me any Direct download link and I'll upload file remotely to Telegram.

**⚡ Features:**
• Direct HTTP/HTTPS downloads
• YouTube, Instagram, TikTok videos  
• Torrent files & magnet links
• Up to 4GB file support
• 500 MB/s blazing speed 🚀

**📝 How to use:**
1️⃣ Send any URL or torrent file
2️⃣ I'll download it super fast
3️⃣ Choose upload type (Doc/Video)
4️⃣ Rename if needed
5️⃣ Done! File uploaded ✅

**👨‍💻 Developer:** {dev}
**📢 Updates:** {channel}"""

    HELP_MESSAGE = """📚 **Help & Commands**

**🔗 Supported Links:**
• Direct downloads (HTTP/HTTPS)
• YouTube videos (up to 4K)
• Instagram posts & reels
• TikTok videos
• Facebook videos
• Twitter/X videos
• Vimeo, Dailymotion
• Torrent files (.torrent)
• Magnet links

**⚙️ Commands:**
/start - Start bot & show menu
/help - Show this help message
/rename - Rename downloaded file
/settings - Bot settings
/status - Your statistics
/about - About this bot

**💡 Tips:**
• Send URL to download automatically
• Send .torrent file to download torrent
• Send magnet link for torrent download
• Original quality preserved (no compression)
• Fast 500 MB/s speed ⚡

**🎬 Video Quality:**
✅ Original resolution (720p, 1080p, 4K)
✅ Original audio (AAC 320kbps)
✅ Original frame rate (24fps, 30fps, 60fps)
✅ Streaming support enabled

**📞 Support:**
**Developer:** {dev}
**Updates:** {channel}"""

    ABOUT_MESSAGE = """ℹ️ **About URL Uploader Bot**

**📦 Version:** 3.0 Pro
**⚡ Speed:** 500 MB/s
**💾 Max Size:** 4 GB
**🎬 Quality:** Original (No compression)

**✨ Features:**
✅ Direct URL downloads
✅ YouTube video downloads (4K)
✅ Instagram, TikTok support
✅ Torrent & magnet links
✅ Custom thumbnails & captions
✅ Auto file type detection
✅ Progress tracking with ETA
✅ Original quality preservation
✅ Streaming support for videos

**🛠️ Technology:**
• Pyrogram - Telegram API
• yt-dlp - Video downloader
• aiohttp - HTTP downloads
• libtorrent - Torrent support
• FFmpeg - Video processing
• MongoDB - Database

**👨‍💻 Developed by:** {dev}
**📢 Updates Channel:** {channel}

**Made with ❤️ for Telegram users!**"""
