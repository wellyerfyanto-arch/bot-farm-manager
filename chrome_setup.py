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
        
        # Railway-specific settings - SANGAT PENTING
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--remote-debugging-port=9222')
        
        # Headless mode untuk server
        chrome_options.add_argument('--headless=new')
        
        # Performance optimizations
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        
        # Security settings
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        
        # Additional options untuk stability
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--no-default-browser-check')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-translate')
        chrome_options.add_argument('--disable-infobars')
        
        # Memory optimizations
        chrome_options.add_argument('--memory-pressure-off')
        chrome_options.add_argument('--max_old_space_size=512')
        
        # Set user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Cari Chrome binary dengan approach yang lebih agresif
        chrome_path = find_chrome_binary()
        if chrome_path:
            chrome_options.binary_location = chrome_path
            logger.info(f"Using Chrome binary at: {chrome_path}")
        else:
            logger.error("Chrome binary not found after aggressive search!")
            # Jangan raise error di sini, biarkan webdriver_manager handle
            
        # Setup service dengan webdriver_manager
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
    """Cari Chrome binary di system dengan approach yang lebih komprehensif"""
    logger.info("Searching for Chrome binary...")
    
    # List semua path yang mungkin
    possible_paths = [
        # Standard Linux paths
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/chromium-browser',
        '/usr/bin/chromium',
        '/usr/local/bin/chrome',
        '/opt/google/chrome/chrome',
        '/snap/bin/chromium',
        
        # Railway-specific paths
        '/app/.apt/usr/bin/google-chrome',
        '/app/.apt/usr/bin/google-chrome-stable',
        '/app/.apt/usr/bin/chromium-browser',
        
        # Alternative paths
        '/usr/lib/chromium-browser/chromium-browser',
        '/usr/lib64/chromium-browser/chromium-browser',
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Found Chrome at: {path}")
            # Test if executable
            if os.access(path, os.X_OK):
                logger.info(f"Chrome is executable: {path}")
                return path
            else:
                logger.warning(f"Chrome found but not executable: {path}")
    
    # Coba dengan which command
    try:
        commands = ['google-chrome', 'google-chrome-stable', 'chromium-browser', 'chromium']
        for cmd in commands:
            result = subprocess.run(['which', cmd], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                path = result.stdout.strip()
                if os.path.exists(path):
                    logger.info(f"Found Chrome via which: {path}")
                    return path
    except Exception as e:
        logger.warning(f"Which command failed: {e}")
    
    # Cek environment variables
    env_paths = [
        os.environ.get('CHROME_BIN'),
        os.environ.get('CHROME_PATH'),
        os.environ.get('GOOGLE_CHROME_BIN')
    ]
    
    for env_path in env_paths:
        if env_path and os.path.exists(env_path):
            logger.info(f"Found Chrome via environment variable: {env_path}")
            return env_path
    
    # Last resort: cari di seluruh system (mungkin lambat)
    try:
        result = subprocess.run(['find', '/', '-name', 'chrome', '-type', 'f', '-executable'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line and ('google' in line.lower() or 'chromium' in line.lower()):
                    logger.info(f"Found Chrome via find: {line}")
                    return line
    except Exception as e:
        logger.warning(f"Find command failed: {e}")
    
    logger.error("No Chrome binary found after comprehensive search")
    return None

def create_chrome_service():
    """Create Chrome service dengan multiple fallback strategies"""
    try:
        # Strategy 1: Coba gunakan chromedriver dari system PATH
        try:
            from selenium.webdriver.chrome.service import Service as ChromeService
            service = ChromeService()
            logger.info("Using system chromedriver")
            return service
        except Exception as e:
            logger.warning(f"System chromedriver failed: {e}")
        
        # Strategy 2: Gunakan webdriver_manager
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service as ChromeService
            
            # Force specific version untuk compatibility
            driver_path = ChromeDriverManager().install()
            service = ChromeService(driver_path)
            logger.info(f"Using webdriver_manager chromedriver: {driver_path}")
            return service
        except Exception as e:
            logger.warning(f"webdriver_manager failed: {e}")
        
        # Strategy 3: Cari chromedriver manual
        chromedriver_path = find_chromedriver()
        if chromedriver_path:
            from selenium.webdriver.chrome.service import Service as ChromeService
            service = ChromeService(chromedriver_path)
            logger.info(f"Using manual chromedriver: {chromedriver_path}")
            return service
        
        # Strategy 4: Final fallback
        from selenium.webdriver.chrome.service import Service as ChromeService
        logger.info("Using default ChromeService")
        return ChromeService()
        
    except Exception as e:
        logger.error(f"All Chrome service strategies failed: {e}")
        raise

def find_chromedriver():
    """Cari chromedriver di system"""
    possible_paths = [
        '/usr/local/bin/chromedriver',
        '/usr/bin/chromedriver',
        '/opt/chromedriver',
        '/app/.apt/usr/bin/chromedriver',
        './chromedriver',
        'chromedriver'
    ]
    
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    # Coba dengan which command
    try:
        result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            path = result.stdout.strip()
            if os.path.exists(path):
                return path
    except:
        pass
    
    return None

def check_chrome_availability():
    """Check if Chrome is available in the system"""
    logger.info("Checking Chrome availability...")
    
    # Cek binary dulu
    chrome_path = find_chrome_binary()
    if not chrome_path:
        logger.warning("Chrome binary not found")
        return False
    
    # Test jika Chrome bisa dijalankan
    try:
        result = subprocess.run([chrome_path, '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_info = result.stdout.strip()
            logger.info(f"Chrome is available: {version_info}")
            
            # Test basic functionality
            try:
                driver = setup_chrome_driver()
                driver.quit()
                logger.info("Chrome functionality test passed")
                return True
            except Exception as e:
                logger.warning(f"Chrome functionality test failed: {e}")
                return False
        else:
            logger.warning(f"Chrome version check failed: {result.stderr}")
            return False
    except Exception as e:
        logger.warning(f"Chrome version check failed: {e}")
        return False
