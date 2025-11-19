import logging
import subprocess
import os

logger = logging.getLogger(__name__)

def initialize_chrome_environment():
    """Initialize Chrome environment saat aplikasi start"""
    logger.info("Initializing Chrome environment...")
    
    # Cek dependencies
    try:
        # Test Chrome
        result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Chrome detected: {result.stdout.strip()}")
        else:
            logger.error("Chrome not working properly")
            
        # Test chromedriver
        result = subprocess.run(['chromedriver', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Chromedriver detected: {result.stdout.strip()}")
        else:
            logger.warning("Chromedriver not found")
            
    except Exception as e:
        logger.error(f"Chrome environment check failed: {e}")
    
    logger.info("Chrome environment initialization completed")

if __name__ == "__main__":
    initialize_chrome_environment()
