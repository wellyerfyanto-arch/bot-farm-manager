import os
import logging
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

def setup_chrome_driver():
    """Setup Chrome driver dengan fallback yang lebih robust"""
    try:
        # Cek apakah Chrome tersedia
        if not check_chrome_availability():
            logger.error("Chrome not available, cannot setup driver")
            raise RuntimeError("Chrome not available in system")
        
        # Setup Chrome options untuk Railway
        chrome_options = Options()
        
        # Railway-specific settings
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--remote-debugging-port=9222')
        
        # Headless mode untuk Railway
        chrome_options.add_argument('--headless=new')
        
        # Performance optimizations
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-background-timer-throttling')
        
        # Security settings
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        
        # Additional options untuk stability
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--no-default-browser-check')
        chrome_options.add_argument('--disable-default-apps')
        
        # Set user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Gunakan Chrome dari path yang mungkin
        chrome_path = find_chrome_path()
        if chrome_path:
            chrome_options.binary_location = chrome_path
            logger.info(f"Using Chrome at: {chrome_path}")
        
        # Setup service - gunakan system chromedriver jika ada
        service = None
        try:
            # Coba gunakan chromedriver dari system
            from selenium.webdriver.chrome.service import Service as ChromeService
            service = ChromeService()
        except:
            # Fallback ke webdriver_manager
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
            except Exception as e:
                logger.warning(f"webdriver_manager failed: {e}")
                # Final fallback - service tanpa parameter
                service = Service()
        
        # Create driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set timeouts
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(10)
        
        logger.info("Chrome driver setup successfully")
        return driver
        
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver: {e}")
        raise

def find_chrome_path():
    """Cari path Chrome di system"""
    possible_paths = [
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable', 
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/usr/bin/chrome',
        '/usr/local/bin/chrome'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Coba dengan which command
    try:
        result = subprocess.run(['which', 'google-chrome'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    return None

def check_chrome_availability():
    """Check if Chrome is available in the system"""
    chrome_path = find_chrome_path()
    if chrome_path:
        logger.info(f"Chrome found at: {chrome_path}")
        return True
    
    logger.warning("Chrome not found in system")
    return False
