import os
import logging
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

def setup_chrome_driver():
    """Setup Chrome/Chromium driver untuk Railway"""
    try:
        logger.info("Setting up Chrome/Chromium driver for Railway...")
        
        # Setup Chrome options
        chrome_options = Options()
        
        # Railway-specific settings
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--remote-debugging-port=9222')
        
        # Performance & Security options
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--no-default-browser-check')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Set user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Gunakan system chromedriver (dari apt installation)
        chromedriver_path = find_system_chromedriver()
        if not chromedriver_path:
            raise RuntimeError("System chromedriver not found")
            
        logger.info(f"Using system chromedriver: {chromedriver_path}")
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set timeouts
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(10)
        
        logger.info("Chrome driver setup successfully with system chromedriver")
        return driver
        
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver: {e}")
        raise

def find_system_chromedriver():
    """Cari chromedriver di system paths"""
    possible_paths = [
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver',
        '/usr/lib/chromium-browser/chromedriver',
        '/snap/bin/chromium.chromedriver'
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            logger.info(f"Found executable chromedriver at: {path}")
            return path
    
    # Coba dengan which command
    try:
        result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            path = result.stdout.strip()
            if os.path.exists(path):
                logger.info(f"Found chromedriver via which: {path}")
                return path
    except Exception as e:
        logger.warning(f"Which command failed: {e}")
    
    logger.error("No system chromedriver found")
    return None

def check_chrome_availability():
    """Check if Chrome/Chromium is available in the system"""
    try:
        # Cek Chromium (bukan google-chrome)
        chromium_result = subprocess.run(['chromium', '--version'], capture_output=True, text=True, timeout=10)
        if chromium_result.returncode == 0:
            logger.info(f"Chromium available: {chromium_result.stdout.strip()}")
            chrome_available = True
        else:
            # Fallback: cek google-chrome
            chrome_result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True, timeout=10)
            if chrome_result.returncode == 0:
                logger.info(f"Chrome available: {chrome_result.stdout.strip()}")
                chrome_available = True
            else:
                logger.warning("Both Chromium and Chrome version checks failed")
                chrome_available = False
        
        # Cek chromedriver
        driver_result = subprocess.run(['chromedriver', '--version'], capture_output=True, text=True, timeout=10)
        if driver_result.returncode == 0:
            logger.info(f"Chromedriver available: {driver_result.stdout.strip()}")
            driver_available = True
        else:
            logger.warning("Chromedriver version check failed")
            driver_available = False
            
        return chrome_available and driver_available
        
    except FileNotFoundError as e:
        logger.warning(f"Browser binary not found: {e}")
        return False
    except Exception as e:
        logger.warning(f"Chrome availability check failed: {e}")
        return False

def get_browser_info():
    """Get detailed browser information untuk debug"""
    info = {
        'chromium_available': False,
        'chrome_available': False,
        'chromedriver_available': False,
        'chromium_version': None,
        'chrome_version': None,
        'chromedriver_version': None,
        'environment_variables': {
            'CHROME_BIN': os.environ.get('CHROME_BIN'),
            'CHROME_PATH': os.environ.get('CHROME_PATH'),
            'CHROMEDRIVER_PATH': os.environ.get('CHROMEDRIVER_PATH')
        }
    }
    
    try:
        # Check Chromium
        result = subprocess.run(['chromium', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            info['chromium_available'] = True
            info['chromium_version'] = result.stdout.strip()
        
        # Check Chrome
        result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            info['chrome_available'] = True
            info['chrome_version'] = result.stdout.strip()
        
        # Check Chromedriver
        result = subprocess.run(['chromedriver', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            info['chromedriver_available'] = True
            info['chromedriver_version'] = result.stdout.strip()
            
    except Exception as e:
        logger.error(f"Error getting browser info: {e}")
    
    return info
