import os
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

class DeviceController:
    def __init__(self, device_id, config, profile_manager):
        self.device_id = device_id
        self.config = config
        self.profile_manager = profile_manager
        self.driver = None
        self.current_profile = None
        self.current_task = None
        self.session_start_time = None
        self.is_active = False
        self.google_login_success = False
        
        # Device capabilities
        self.capabilities = {
            'browser_name': 'chrome',
            'max_session_duration': config.get('max_session_duration', 3600),
            'proxy_enabled': config.get('proxy_enabled', False),
            'headless': config.get('headless', False),
            'save_session': config.get('save_session', True)  # New config
        }

    def _setup_chrome_options(self, profile):
        """Setup Chrome options dengan profile"""
        chrome_options = Options()
        
        # Basic settings
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Headless mode
        if self.capabilities['headless']:
            chrome_options.add_argument('--headless=new')
        
        # Device type
        if self.config.get('type') == 'mobile':
            chrome_options.add_argument('--window-size=375,812')
            mobile_emulation = {
                "deviceMetrics": { "width": 375, "height": 812, "pixelRatio": 3.0 },
                "userAgent": UserAgent().android
            }
            chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        else:
            chrome_options.add_argument('--window-size=1920,1080')
        
        # Profile directory - SELALU gunakan profile path untuk session persistence
        if profile and profile.get('profile_path'):
            chrome_options.add_argument(f'--user-data-dir={profile["profile_path"]}')
        
        # Anti-detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        return chrome_options

    def _save_session_cookies(self):
        """Save session cookies untuk persistence"""
        if not self.capabilities['save_session']:
            return
        
        try:
            cookies = self.driver.get_cookies()
            self.profile_manager.save_cookies(self.device_id, cookies)
        except Exception as e:
            logger.warning(f"⚠️ Could not save cookies for {self.device_id}: {e}")

    def _load_session_cookies(self):
        """Load session cookies untuk persistence"""
        if not self.capabilities['save_session']:
            return False
        
        try:
            cookies = self.profile_manager.load_cookies(self.device_id)
            if cookies:
                # Clear existing cookies first
                self.driver.delete_all_cookies()
                
                # Add saved cookies
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.warning(f"⚠️ Could not add cookie: {e}")
                
                # Refresh to apply cookies
                self.driver.refresh()
                return True
        except Exception as e:
            logger.warning(f"⚠️ Could not load cookies for {self.device_id}: {e}")
        
        return False

    def _check_google_logged_in(self):
        """Check if already logged in to Google"""
        try:
            # Try to access Gmail or Google Account
            self.driver.get("https://mail.google.com")
            time.sleep(2)
            
            # Check if we're redirected to login page or stay in inbox
            if "mail.google.com" in self.driver.current_url and "accountchooser" not in self.driver.current_url:
                logger.info(f"✅ {self.device_id} already logged in to Google (Gmail check)")
                return True
            
            # Alternative check: Google Account page
            self.driver.get("https://myaccount.google.com")
            time.sleep(2)
            
            if "myaccount.google.com" in self.driver.current_url:
                logger.info(f"✅ {self.device_id} already logged in to Google (Account check)")
                return True
                
        except Exception as e:
            logger.warning(f"⚠️ Error checking Google login status: {e}")
        
        return False

    def _login_google(self, email, password):
        """Login ke Google dengan email dan password"""
        try:
            logger.info(f"🔐 Device {self.device_id} attempting Google login: {email}")
            
            self.driver.get("https://accounts.google.com/signin")
            time.sleep(3)
            
            # Input email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "identifierId"))
            )
            email_field.clear()
            
            # Type like human
            for char in email:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            next_button = self.driver.find_element(By.ID, "identifierNext")
            next_button.click()
            time.sleep(3)
            
            # Input password
            password_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "password"))
            )
            password_field.clear()
            
            for char in password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            password_next = self.driver.find_element(By.ID, "passwordNext")
            password_next.click()
            time.sleep(5)
            
            # Check if login successful
            if self._check_google_logged_in():
                logger.info(f"✅ Google login successful for {email}")
                self.google_login_success = True
                
                # Save session and mark as logged in
                self._save_session_cookies()
                self.profile_manager.mark_google_logged_in(self.device_id, email)
                
                return True
            else:
                logger.warning(f"⚠️ Google login may have failed for {email}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Google login failed for {email}: {e}")
            return False

    def start_session(self, profile, task_config):
        """Start browser session dengan login Google"""
        try:
            self.current_profile = profile
            self.current_task = task_config
            
            # Setup Chrome
            chrome_options = self._setup_chrome_options(profile)
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Check if already logged in via profile
            if self.profile_manager.is_google_logged_in(self.device_id):
                logger.info(f"🔄 Checking existing Google session for {self.device_id}")
                
                # Try to load cookies first
                if self._load_session_cookies():
                    time.sleep(2)
                    
                # Check if still logged in
                if self._check_google_logged_in():
                    self.google_login_success = True
                    logger.info(f"✅ Resumed Google session for {self.device_id}")
                else:
                    # Session expired, need to login again
                    logger.info(f"🔄 Google session expired for {self.device_id}")
                    self.google_login_success = False
            
            # Login Google jika belum login dan ada akun
            if not self.google_login_success:
                google_account = self.config.get('google_account')
                if google_account and google_account.get('email') and google_account.get('password'):
                    self._login_google(google_account['email'], google_account['password'])
            
            # Execute task
            self._execute_task(task_config)
            
            self.session_start_time = time.time()
            self.is_active = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Device {self.device_id} failed to start: {e}")
            self.is_active = False
            return False

    # ... (rest of the existing methods remain the same)

    def stop_session(self):
        """Stop device session dan save state"""
        try:
            # Save session before quitting
            if self.google_login_success and self.capabilities['save_session']:
                self._save_session_cookies()
            
            if self.driver:
                self.driver.quit()
        except:
            pass
        
        self.driver = None
        self.is_active = False
        self.session_start_time = None
        logger.info(f"🛑 Device {self.device_id} session stopped")