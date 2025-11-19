import os
import logging
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

def setup_chrome_driver():
    """Setup Chrome driver using webdriver_manager for automatic version handling."""
    try:
        logger.info("Setting up Chrome driver using webdriver_manager...")
        
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
        
        # Use webdriver_manager to handle ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set timeouts
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(10)
        
        logger.info("Chrome driver setup successfully using webdriver_manager")
        return driver
        
    except Exception as e:
        logger.error(f"Failed to setup Chrome driver with webdriver_manager: {e}")
        raise

def check_chrome_availability():
    """Check if Chrome is available in the system."""
    try:
        # Try to get Chrome version
        result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"Chrome is available: {result.stdout.strip()}")
            return True
        else:
            logger.warning("Chrome version check failed.")
            return False
    except Exception as e:
        logger.warning(f"Chrome availability check failed: {e}")
        return False
