def _setup_chrome_driver(self, profile):
    """Setup Chrome driver dengan fallback robust"""
    try:
        # Coba setup Chrome driver
        from chrome_setup import setup_chrome_driver
        driver = setup_chrome_driver()
        
        # Apply profile settings jika ada
        if profile and profile.get('profile_path'):
            logger.info("Profile path available: %s", profile['profile_path'])
        
        return driver
        
    except Exception as e:
        logger.error("Failed to setup Chrome driver for %s: %s", self.device_id, e)
        
        # Fallback ke simple browser simulator
        try:
            from simple_browser import SimpleBrowser
            logger.info("Using SimpleBrowser fallback for %s", self.device_id)
            return SimpleBrowser(self.device_id)
        except Exception as fallback_error:
            logger.error("Fallback also failed for %s: %s", self.device_id, fallback_error)
            # Final fallback - return None dan biarkan system handle
            return None
