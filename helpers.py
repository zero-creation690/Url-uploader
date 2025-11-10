import time
import asyncio
import math
from typing import Optional
from pyrogram.errors import MessageNotModified, FloodWait
from config import Config  # Import your Config class to use SPEED_LIMIT

class Progress:
    """Enhanced progress tracker for downloads, uploads, and torrents"""
    
    def __init__(self, client, message):
        self.client = client
        self.message = message
        self.start_time = time.time()
        self.last_update = 0
        self.update_interval = 2  # Update every 2 seconds for faster feedback
        self.last_text = ""
        self.last_percentage = 0
        
    async def progress_callback(self, current, total, status="Processing"):
        """
        Enhanced progress callback for pyrogram
        Works with downloads, uploads, and torrents
        """
        now = time.time()
        
        if now - self.last_update < self.update_interval:
            return
        
        try:
            elapsed = now - self.start_time
            
            if current == 0 or elapsed == 0 or total == 0:
                return
            
            # Calculate metrics
            speed = current / elapsed
            percentage = (current * 100) / total
            eta_seconds = (total - current) / speed if speed > 0 else 0
            
            if abs(percentage - self.last_percentage) < 1 and percentage < 99:
                return
            
            self.last_percentage = percentage
            
            # Progress bar
            filled = int(percentage / 5)
            progress_bar = "█" * filled + "░" * (20 - filled)
            
            # Format sizes
            current_formatted = humanbytes(current)
            total_formatted = humanbytes(total)
            speed_formatted = humanbytes(int(speed))
            
            text = (
                f"**{status}**\n\n"
                f"{progress_bar} `{percentage:.1f}%`\n\n"
                f"📦 **Size:** {current_formatted} / {total_formatted}\n"
                f"⚡ **Speed:** {speed_formatted}/s\n"
                f"⏱️ **ETA:** {format_time(eta_seconds)}\n"
                f"🕐 **Elapsed:** {format_time(elapsed)}"
            )
            
            if text != self.last_text:
                await self.message.edit_text(text)
                self.last_text = text
                self.last_update = now
                
        except MessageNotModified:
            pass
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            pass

class TorrentProgress(Progress):
    """Specialized progress tracker for torrent downloads"""
    
    def __init__(self, client, message):
        super().__init__(client, message)
        self.update_interval = 3
        
    async def torrent_progress_callback(self, current, total, extra_info=""):
        now = time.time()
        
        if now - self.last_update < self.update_interval:
            return
        
        try:
            elapsed = now - self.start_time
            
            if current == 0 or total == 0:
                text = (
                    f"**📥 Downloading Torrent**\n\n"
                    f"⏳ Connecting to peers...\n"
                    f"{extra_info}"
                )
                await self.message.edit_text(text)
                self.last_update = now
                return
            
            speed = current / elapsed if elapsed > 0 else 0
            percentage = (current * 100) / total
            eta_seconds = (total - current) / speed if speed > 0 else 0
            
            filled = int(percentage / 5)
            progress_bar = "█" * filled + "░" * (20 - filled)
            
            current_formatted = humanbytes(current)
            total_formatted = humanbytes(total)
            speed_formatted = humanbytes(int(speed))
            
            text = (
                f"**📥 Downloading Torrent**\n\n"
                f"{progress_bar} `{percentage:.1f}%`\n\n"
                f"📦 **Size:** {current_formatted} / {total_formatted}\n"
                f"⚡ **Speed:** {speed_formatted}/s\n"
                f"⏱️ **ETA:** {format_time(eta_seconds)}\n"
                f"🕐 **Elapsed:** {format_time(elapsed)}\n"
                f"{extra_info}"
            )
            
            if text != self.last_text:
                await self.message.edit_text(text)
                self.last_text = text
                self.last_update = now
                
        except MessageNotModified:
            pass
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception:
            pass

def format_time(seconds):
    if seconds < 0:
        return "calculating..."
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"

def humanbytes(size):
    if not size or size < 0:
        return "0 B"
    power = 1024
    n = 0
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    while size >= power and n < len(units) - 1:
        size /= power
        n += 1
    return f"{size:.2f} {units[n]}"

async def speed_limiter(chunk_size, speed_limit=Config.SPEED_LIMIT):
    """
    Limit download/upload speed dynamically using Config.SPEED_LIMIT
    """
    if speed_limit <= 0:
        return
    delay = chunk_size / speed_limit
    if delay > 0:
        await asyncio.sleep(delay)

# --- Other utility functions remain unchanged ---
def is_url(text):
    if not text or not isinstance(text, str):
        return False
    text = text.strip().lower()
    valid_schemes = ('http://', 'https://', 'ftp://', 'ftps://', 'www.', 'magnet:?')
    return text.startswith(valid_schemes)

def is_magnet_link(text):
    if not text or not isinstance(text, str):
        return False
    return text.strip().lower().startswith('magnet:?')

def is_torrent_file(text):
    if not text or not isinstance(text, str):
        return False
    return text.strip().lower().endswith('.torrent')

def sanitize_filename(filename, max_length=255):
    if not filename:
        return "download"
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    filename = ''.join(char for char in filename if ord(char) >= 32)
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        if ext:
            max_name_length = max_length - len(ext) - 1
            filename = name[:max_name_length] + '.' + ext
        else:
            filename = filename[:max_length]
    filename = filename.strip('. ')
    if not filename:
        return "download"
    return filename

def get_file_extension(url_or_filename):
    if not url_or_filename:
        return ""
    clean_url = url_or_filename.split('?')[0]
    if '.' in clean_url:
        ext = clean_url.rsplit('.', 1)[-1].lower()
        if len(ext) <= 5 and ext.isalnum():
            return f".{ext}"
    return ""

def format_torrent_info(peers=0, seeds=0, download_rate=0, upload_rate=0):
    info_parts = []
    if peers >= 0:
        info_parts.append(f"👥 **Peers:** {peers}")
    if seeds >= 0:
        info_parts.append(f"🌱 **Seeds:** {seeds}")
    if download_rate > 0:
        info_parts.append(f"⬇️ **Down:** {humanbytes(int(download_rate))}/s")
    if upload_rate > 0:
        info_parts.append(f"⬆️ **Up:** {humanbytes(int(upload_rate))}/s")
    return "\n".join(info_parts) if info_parts else ""

def validate_file_size(size, max_size):
    if size <= 0:
        return False, "Invalid file size"
    if size > max_size:
        return False, f"File size ({humanbytes(size)}) exceeds limit ({humanbytes(max_size)})"
    return True, "Valid"

async def retry_on_flood(func, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            return await func()
        except FloodWait as e:
            retries += 1
            if retries >= max_retries:
                raise
            await asyncio.sleep(e.value)
        except Exception:
            raise
    return None
