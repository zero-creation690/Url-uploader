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
    SESSION_STR = os.environ.get("SESSION_STR", "BQE1leIAwLolJnNNwcuPKFW7hKRrfqZdz26eFNRZdEiv1h3yHHcDStIp0I-ScPuhMzSkTP6xUMpBvtPle0mdVKcUxcQxIyOHrLY4HqXgWysXl5vtSRAa7DMrzuM2CVsDA2On43gHkfOgg70K6ommgYI9rBPsW547vfTTBmzluMnQnpu2ZlSZH5kgVFPsQKdexBPy6Yf3hf8Fx1ektQdg2oDbaCBHDQJF-Z8E6-W2chObXsctL7t0pFAOh2Oi6qHISV4GPLf9o3Jy8COX61Olm12onwPZhKX75MrOgx-21Ny0802pjpEQs1Yvn4n1jO1J2b8XGBAimU6d7NN7g9oz4fwu4mntaAAAAAHgiIN5AQ")
    
    # Update channel
    UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", "https://t.me/zerodevbro")
    DEVELOPER = "@Zeroboy216"
    
    # Download/Upload settings
    MAX_FILE_SIZE = 4 * 1024 * 1024 * 1024  # 4 GB
    SPEED_LIMIT = 200 * 1024 * 1024  # 200 MB/s (super fast!)
    CHUNK_SIZE = 1024 * 1024  # 1 MB chunks for faster transfer
    
    # Download directory
    DOWNLOAD_DIR = "downloads"
    
    # Torrent settings
    TORRENT_DOWNLOAD_PATH = "downloads/torrents"
    TORRENT_SEED_TIME = 0  # Don't seed after download
