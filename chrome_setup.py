import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

def setup_chrome_driver():
    """Setup Chrome driver yang compatible dengan Railway"""
    try:
        # Setup Chrome options untuk Railway
        chrome_options = Options()
        
        # Railway-specific settings
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--remote-debugging-port=9222')
        
        # Headless mode untuk Railway (wajib)
        chrome_options.add_argument('--headless=new')
        
        # Performance optimizations
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        
        # Memory optimizations
        chrome_options.add_argument('--memory-pressure-off')
        chrome_options.add_argument('--max_old_space_size=512')
        
        # Security settings
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        
        # Logging settings
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--silent')
        
        # Additional options untuk stability
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--no-default-browser-check')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-translate')
        chrome_options.add_argument('--disable-infobars')
        
        # Set user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Setup Chrome driver service
        service = Service(ChromeDriverManager().install())
        
        # Create driver dengan error handling
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set timeouts
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(10)
        
        logger.info("✅ Chrome driver setup successfully for Railway")
        return driver
        
    except Exception as e:
        logger.error(f"❌ Failed to setup Chrome driver: {e}")
        raise

def check_chrome_availability():
    """Check if Chrome is available in the system"""
    try:
        # Try to create a simple Chrome instance
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.quit()
        return True
    except Exception as e:
        logger.error(f"❌ Chrome not available: {e}")
        return False