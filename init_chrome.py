import logging
import subprocess
import os
import sys

logger = logging.getLogger(__name__)

def install_chrome():
    """Install Chrome secara manual jika tidak terdeteksi"""
    logger.info("Attempting to install Chrome...")
    
    try:
        # Update package list
        subprocess.run(['apt-get', 'update'], check=True, capture_output=True)
        
        # Install dependencies
        dependencies = [
            'wget', 'gnupg', 'libnss3-dev', 'libgconf-2-4', 
            'libxss1', 'libappindicator1', 'libindicator7', 
            'fonts-liberation', 'xvfb'
        ]
        subprocess.run(['apt-get', 'install', '-y'] + dependencies, check=True, capture_output=True)
        
        # Download and install Chrome
        chrome_install_commands = [
            'wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -',
            'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list',
            'apt-get update',
            'apt-get install -y google-chrome-stable'
        ]
        
        for cmd in chrome_install_commands:
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
        
        logger.info("Chrome installation completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Chrome installation failed: {e}")
        return False

def install_chromedriver():
    """Install chromedriver secara manual"""
    logger.info("Attempting to install chromedriver...")
    
    try:
        # Get latest chromedriver version
        version_result = subprocess.run(
            ['curl', '-s', 'https://chromedriver.storage.googleapis.com/LATEST_RELEASE'],
            capture_output=True, text=True, check=True
        )
        version = version_result.stdout.strip()
        
        # Download and install
        download_url = f"https://chromedriver.storage.googleapis.com/{version}/chromedriver_linux64.zip"
        
        commands = [
            f"wget -q -O /tmp/chromedriver.zip {download_url}",
            "unzip /tmp/chromedriver.zip -d /usr/local/bin/",
            "chmod +x /usr/local/bin/chromedriver",
            "rm /tmp/chromedriver.zip"
        ]
        
        for cmd in commands:
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
        
        logger.info(f"Chromedriver installation completed: {version}")
        return True
        
    except Exception as e:
        logger.error(f"Chromedriver installation failed: {e}")
        return False

def initialize_chrome_environment():
    """Initialize Chrome environment saat aplikasi start"""
    logger.info("Initializing Chrome environment...")
    
    # Cek Chrome availability
    try:
        from chrome_setup import check_chrome_availability
        
        if not check_chrome_availability():
            logger.warning("Chrome not available, attempting installation...")
            
            # Try to install Chrome
            if install_chrome():
                logger.info("Chrome installation successful, re-checking availability...")
                if check_chrome_availability():
                    logger.info("Chrome is now available after installation")
                else:
                    logger.error("Chrome still not available after installation")
            else:
                logger.error("Chrome installation failed")
        else:
            logger.info("Chrome is already available")
            
    except Exception as e:
        logger.error(f"Chrome environment initialization failed: {e}")
    
    # Cek chromedriver
    try:
        result = subprocess.run(['chromedriver', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Chromedriver detected: {result.stdout.strip()}")
        else:
            logger.warning("Chromedriver not found, attempting installation...")
            install_chromedriver()
    except Exception as e:
        logger.error(f"Chromedriver check failed: {e}")
    
    logger.info("Chrome environment initialization completed")

if __name__ == "__main__":
    initialize_chrome_environment()
