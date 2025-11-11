import os
import aiohttp
import asyncio
import yt_dlp
import libtorrent as lt
from config import Config
from helpers import sanitize_filename
import time
import shutil
from pathlib import Path
import urllib.parse

class Downloader:
    def __init__(self):
        self.download_dir = Config.DOWNLOAD_DIR
        self.torrent_dir = Config.TORRENT_DOWNLOAD_PATH
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.torrent_dir, exist_ok=True)
    
    async def download_file(self, url, filename=None, progress_callback=None):
        """Download file from URL with optimized speed and better error handling"""
        try:
            # Increased timeout and optimized settings
            timeout = aiohttp.ClientTimeout(total=None, connect=120, sock_read=120)
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                force_close=False
            )
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            async with aiohttp.ClientSession(
                timeout=timeout, 
                headers=headers,
                connector=connector
            ) as session:
                async with session.get(url, allow_redirects=True) as response:
                    if response.status != 200:
                        return None, f"Failed to download: HTTP {response.status}"
                    
                    total_size = int(response.headers.get('content-length', 0))
                    
                    if total_size > Config.MAX_FILE_SIZE:
                        return None, "File size exceeds 4GB limit"
                    
                    # Get filename from headers or use provided
                    if not filename:
                        content_disp = response.headers.get('content-disposition', '')
                        if 'filename=' in content_disp:
                            filename = content_disp.split('filename=')[1].strip('"\'')
                        else:
                            filename = urllib.parse.unquote(url.split('/')[-1].split('?')[0]) or 'downloaded_file'
                    
                    filename = sanitize_filename(filename)
                    filepath = os.path.join(self.download_dir, filename)
                    
                    downloaded = 0
                    start_time = time.time()
                    last_update = 0
                    
                    # Larger chunk size for faster downloads (10MB chunks)
                    chunk_size = 10 * 1024 * 1024
                    
                    with open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Progress callback every 1 second
                            current_time = time.time()
                            if progress_callback and (current_time - last_update) >= 1:
                                last_update = current_time
                                speed = downloaded / (current_time - start_time) / (1024 * 1024)
                                await progress_callback(downloaded, total_size, f"Downloading ({speed:.1f} MB/s)")
                            
                            # No artificial delay - let it run at full speed
                    
                    return filepath, None
                    
        except asyncio.TimeoutError:
            return None, "Download timeout - file too large or connection too slow"
        except Exception as e:
            return None, f"Download error: {str(e)}"
    
    async def download_ytdlp(self, url, progress_callback=None):
        """Download using yt-dlp with BEST quality - Fixed path handling"""
        try:
            # Sanitize output template path
            output_template = os.path.join(self.download_dir, '%(title)s.%(ext)s')
            
            ydl_opts = {
                'outtmpl': output_template,
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'quiet': False,
                'no_warnings': False,
                'writethumbnail': False,
                'no_post_overwrites': True,
                'ignoreerrors': False,
                # Enhanced headers
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate',
                },
                # Better extractor args
                'extractor_args': {
                    'tiktok': {
                        'api_hostname': 'api22-normal-c-useast2a.tiktokv.com'
                    }
                },
                # Optimized retry and connection settings
                'retries': 10,
                'fragment_retries': 10,
                'skip_unavailable_fragments': True,
                'concurrent_fragment_downloads': 5,  # Download 5 fragments at once
                'source_address': '0.0.0.0',
                # File system safety
                'restrictfilenames': True,  # Avoid problematic characters
                'windowsfilenames': True,   # Windows-safe filenames
            }
            
            loop = asyncio.get_event_loop()
            
            def download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    
                    # Get the actual downloaded filename
                    filename = ydl.prepare_filename(info)
                    
                    # Check for merged file
                    base = os.path.splitext(filename)[0]
                    possible_files = [
                        filename,
                        f"{base}.mp4",
                        f"{base}.mkv",
                        f"{base}.webm"
                    ]
                    
                    for pf in possible_files:
                        if os.path.exists(pf):
                            return pf, info.get('title', 'Video')
                    
                    # If nothing found, return the prepared filename anyway
                    return filename, info.get('title', 'Video')
            
            filepath, title = await loop.run_in_executor(None, download)
            
            # Verify file exists and is valid
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                return filepath, None
            else:
                return None, "Download completed but file not found or empty"
                
        except Exception as e:
            error_msg = str(e)
            if "HTTP Error 403" in error_msg:
                return None, "Access denied - video may be private or region-locked"
            elif "Video unavailable" in error_msg:
                return None, "Video is unavailable or has been removed"
            else:
                return None, f"Download error: {error_msg}"
    
    async def download_torrent(self, magnet_or_file, progress_callback=None):
        """Download torrent with better path handling"""
        try:
            ses = lt.session()
            ses.listen_on(6881, 6891)
            
            # Optimized settings for faster downloads
            settings = {
                'user_agent': 'libtorrent/2.0',
                'announce_to_all_trackers': True,
                'announce_to_all_tiers': True,
                'auto_managed': True,
                'max_connections': 200,
                'max_uploads': 20,
            }
            ses.apply_settings(settings)
            
            params = {
                'save_path': self.torrent_dir,
                'storage_mode': lt.storage_mode_t.storage_mode_sparse,
            }
            
            # Handle magnet or file
            if magnet_or_file.startswith('magnet:'):
                handle = lt.add_magnet_uri(ses, magnet_or_file, params)
            else:
                # Verify torrent file exists
                if not os.path.exists(magnet_or_file):
                    return None, f"Torrent file not found: {magnet_or_file}"
                    
                info = lt.torrent_info(magnet_or_file)
                handle = ses.add_torrent({'ti': info, 'save_path': self.torrent_dir})
            
            # Wait for metadata with timeout
            timeout_counter = 0
            while not handle.has_metadata():
                await asyncio.sleep(1)
                timeout_counter += 1
                if timeout_counter > 60:  # 60 second timeout
                    return None, "Timeout waiting for torrent metadata"
            
            info = handle.get_torrent_info()
            name = info.name()
            
            # Download with progress
            last_progress = -1
            while not handle.is_seed():
                s = handle.status()
                
                progress = s.progress * 100
                download_rate = s.download_rate / 1024 / 1024  # MB/s
                
                # Only update if progress changed
                if progress_callback and abs(progress - last_progress) > 0.1:
                    last_progress = progress
                    await progress_callback(
                        int(s.total_done),
                        int(s.total_wanted),
                        f"Torrenting {progress:.1f}% ({download_rate:.2f} MB/s)"
                    )
                
                await asyncio.sleep(1)
            
            # Get downloaded file/folder path - use Path for better handling
            filepath = Path(self.torrent_dir) / name
            
            # Verify the download
            if not filepath.exists():
                return None, f"Torrent completed but file not found: {filepath}"
            
            # Stop seeding
            ses.remove_torrent(handle)
            
            return str(filepath), None
            
        except Exception as e:
            return None, f"Torrent error: {str(e)}"
    
    async def download(self, url_or_file, filename=None, progress_callback=None):
        """Main download function with better type detection"""
        
        # Validate input
        if not url_or_file:
            return None, "No URL or file provided"
        
        url_or_file_lower = url_or_file.lower()
        
        # Check if it's a magnet link
        if url_or_file.startswith('magnet:'):
            return await self.download_torrent(url_or_file, progress_callback)
        
        # Check if it's a torrent file (path or URL)
        if url_or_file_lower.endswith('.torrent'):
            return await self.download_torrent(url_or_file, progress_callback)
        
        # Check if URL is for video platforms
        video_domains = [
            'youtube.com', 'youtu.be', 'instagram.com', 'facebook.com',
            'twitter.com', 'x.com', 'tiktok.com', 'vimeo.com', 'dailymotion.com',
            'vt.tiktok.com', 'vm.tiktok.com', 'reddit.com', 'twitch.tv'
        ]
        
        is_video_url = any(domain in url_or_file_lower for domain in video_domains)
        
        if is_video_url:
            return await self.download_ytdlp(url_or_file, progress_callback)
        else:
            return await self.download_file(url_or_file, filename, progress_callback)
    
    def cleanup(self, filepath):
        """Remove downloaded file or directory with better error handling"""
        try:
            path = Path(filepath)
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
        except Exception as e:
            print(f"Cleanup error: {e}")

downloader = Downloader()
