"""
Redis Download Utility for Embedded Redis Testing
Downloads Redis executable for development and testing purposes
"""

import os
import sys
import platform
import urllib.request
import zipfile
import tarfile
import shutil
import logging
from pathlib import Path


def get_redis_download_info():
    """Get Redis download information based on platform"""
    system = platform.system().lower()
    
    if system == "windows":
        return {
            "url": "https://github.com/microsoftarchive/redis/releases/download/win-3.0.504/Redis-x64-3.0.504.zip",
            "filename": "Redis-x64-3.0.504.zip",
            "executable": "redis-server.exe",
            "extract_method": "zip"
        }
    elif system == "darwin":  # macOS
        return {
            "url": "https://download.redis.io/redis-stable.tar.gz",
            "filename": "redis-stable.tar.gz", 
            "executable": "redis-server",
            "extract_method": "tar"
        }
    else:  # Linux
        return {
            "url": "https://download.redis.io/redis-stable.tar.gz",
            "filename": "redis-stable.tar.gz",
            "executable": "redis-server", 
            "extract_method": "tar"
        }


def download_redis_for_testing():
    """Download Redis executable for embedded Redis testing"""
    logger = logging.getLogger(__name__)
    
    # Create redis directory in project root
    project_root = Path(__file__).parent.parent.parent.parent
    redis_dir = project_root / "redis"
    redis_dir.mkdir(exist_ok=True)
    
    download_info = get_redis_download_info()
    
    # Check if Redis executable already exists
    redis_executable = redis_dir / download_info["executable"]
    if redis_executable.exists():
        logger.info(f"✅ Redis executable already exists: {redis_executable}")
        return str(redis_executable)
    
    logger.info(f"📥 Downloading Redis for {platform.system()}...")
    
    try:
        # Download Redis
        download_path = redis_dir / download_info["filename"]
        urllib.request.urlretrieve(download_info["url"], download_path)
        logger.info(f"✅ Downloaded: {download_path}")
        
        # Extract Redis
        if download_info["extract_method"] == "zip":
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(redis_dir)
        else:  # tar
            with tarfile.open(download_path, 'r:gz') as tar_ref:
                tar_ref.extractall(redis_dir)
        
        # Find and move Redis executable
        for root, dirs, files in os.walk(redis_dir):
            for file in files:
                if file == download_info["executable"]:
                    source = os.path.join(root, file)
                    destination = redis_dir / download_info["executable"]
                    shutil.move(source, destination)
                    
                    # Make executable on Unix systems
                    if platform.system() != "Windows":
                        os.chmod(destination, 0o755)
                    
                    logger.info(f"✅ Redis executable ready: {destination}")
                    
                    # Clean up download file
                    download_path.unlink()
                    
                    return str(destination)
        
        logger.error("❌ Redis executable not found in downloaded archive")
        return None
        
    except Exception as e:
        logger.error(f"❌ Failed to download Redis: {e}")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Redis Download Utility for Embedded Redis Testing")
    print("=" * 60)
    
    redis_path = download_redis_for_testing()
    
    if redis_path:
        print(f"✅ Success! Redis executable available at: {redis_path}")
        print("\n💡 You can now test embedded Redis functionality!")
        print("   Run: python src/main.py")
    else:
        print("❌ Failed to download Redis executable")
        print("\n💡 Alternative: Install Redis manually")
        print("   Windows: Download from https://github.com/microsoftarchive/redis/releases")
        print("   macOS: brew install redis")
        print("   Linux: sudo apt install redis-server") 