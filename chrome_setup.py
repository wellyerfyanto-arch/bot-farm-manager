import os
import logging
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

def setup_chrome_driver():
    """Setup Chrome driver yang dioptimalkan untuk Railway"""
    try:
        logger.info("Setting up Chrome driver for Railway...")
        
        # Setup Chrome options
        chrome_options = Options()
        
        # Railway-specific settings
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-background-timer-throttling')
        
        # Headless mode untuk server
        chrome_options.add_argument('--headless=new')
        
        # Performance optimizations
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        
        # Security settings
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        
        # Additional options untuk stability
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--no-default-browser-check')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-translate')
        chrome_options.add_argument('--disable-infobars')
        
        # Set user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Cari Chrome binary
        chrome_path = find_chrome_binary()
        if chrome_path:
            chrome_options.binary_location = chrome_path
            logger.info(f"Using Chrome binary at: {chrome_path}")
        else:
            logger.error("Chrome binary not found!")
            raise RuntimeError("Chrome binary not found")
        
        # Setup service
        service = create_chrome_service()
        
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

def find_chrome_binary():
    """Cari Chrome binary di system"""
    possible_paths = [
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium',
        '/usr/local/bin/chrome',
        '/opt/google/chrome/chrome'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found Chrome at: {path}")
            return path
    
    # Coba dengan which command
    try:
        for binary in ['google-chrome', 'google-chrome-stable', 'chromium-browser', 'chromium']:
            result = subprocess.run(['which', binary], capture_output=True, text=True)
            if result.returncode == 0:
                path = result.stdout.strip()
                logger.info(f"Found Chrome via which: {path}")
                return path
    except Exception as e:
        logger.warning(f"Which command failed: {e}")
    
    logger.error("No Chrome binary found in system")
    return None

def create_chrome_service():
    """Create Chrome service dengan fallback"""
    try:
        # Coba gunakan chromedriver dari system
        from selenium.webdriver.chrome.service import Service as ChromeService
        
        # Cari chromedriver
        chromedriver_path = find_chromedriver()
        if chromedriver_path:
            logger.info(f"Using chromedriver at: {chromedriver_path}")
            return ChromeService(executable_path=chromedriver_path)
        else:
            # Fallback ke webdriver_manager
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                logger.info("Using webdriver_manager for chromedriver")
                return Service(ChromeDriverManager().install())
            except Exception as e:
                logger.warning(f"webdriver_manager failed: {e}")
                # Final fallback - service tanpa parameter
                logger.info("Using default ChromeService")
                return ChromeService()
                
    except Exception as e:
        logger.error(f"Failed to create Chrome service: {e}")
        raise

def find_chromedriver():
    """Cari chromedriver di system"""
    possible_paths = [
        '/usr/local/bin/chromedriver',
        '/usr/bin/chromedriver',
        '/opt/chromedriver',
        './chromedriver'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Coba dengan which command
    try:
        result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    
    return None

def check_chrome_availability():
    """Check if Chrome is available in the system"""
    chrome_path = find_chrome_binary()
    if chrome_path:
        # Test jika Chrome bisa dijalankan
        try:
            result = subprocess.run([chrome_path, '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"Chrome is available: {result.stdout.strip()}")
                return True
        except Exception as e:
            logger.warning(f"Chrome version check failed: {e}")
    
    logger.warning("Chrome is not available")
    return False
