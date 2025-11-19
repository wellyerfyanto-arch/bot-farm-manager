import os
import time
import random
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
            'headless': True,
            'save_session': config.get('save_session', True)
        }

    def _setup_chrome_driver(self, profile):
        """Setup Chrome driver dengan comprehensive error handling"""
        try:
            logger.info(f"Setting up Chrome driver for {self.device_id}")
            
            from chrome_setup import setup_chrome_driver, check_chrome_availability, get_browser_info
            
            # Cek ketersediaan Chrome/Chromium secara detail
            browser_info = get_browser_info()
            logger.info(f"Browser info for {self.device_id}: {browser_info}")
            
            if not check_chrome_availability():
                error_msg = f"Chrome not available for {self.device_id}. Browser: {browser_info.get('browser_available')}, Driver: {browser_info.get('chromedriver_available')}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            # Setup Chrome driver
            driver = setup_chrome_driver()
            
            # Apply profile settings jika ada
            if profile and profile.get('profile_path'):
                logger.info(f"Profile path available for {self.device_id}: {profile['profile_path']}")
            
            logger.info(f"Chrome driver setup successful for {self.device_id}")
            return driver
            
        except Exception as e:
            logger.error(f"Chrome setup failed for {self.device_id}: {e}")
            raise RuntimeError(f"Chrome setup failed: {str(e)}")

    def start_session(self, profile, task_config):
        """Start browser session dengan comprehensive error handling"""
        try:
            self.current_profile = profile
            self.current_task = task_config
            
            logger.info(f"Starting session for device {self.device_id}")
            
            # Setup Chrome driver
            self.driver = self._setup_chrome_driver(profile)
            
            if self.driver is None:
                logger.error(f"No driver available for {self.device_id}")
                return False
            
            # Check if already logged in via profile (cookies)
            if self.profile_manager.is_google_logged_in(self.device_id):
                logger.info(f"Checking existing Google session for {self.device_id}")
                
                # Try to load cookies
                if self._load_session_cookies():
                    time.sleep(2)
                    
                # Check if still logged in
                if self._check_google_logged_in():
                    self.google_login_success = True
                    logger.info(f"Resumed Google session for {self.device_id}")
                else:
                    # Session expired, need to login again
                    logger.info(f"Google session expired for {self.device_id}")
                    self.google_login_success = False
            
            # Login Google jika belum login dan ada akun
            if not self.google_login_success:
                google_account = self.config.get('google_account')
                if google_account and google_account.get('email') and google_account.get('password'):
                    logger.info(f"Attempting Google login for {self.device_id}")
                    login_success = self._login_google(google_account['email'], google_account['password'])
                    if login_success:
                        self.google_login_success = True
                        logger.info(f"Google login successful for {self.device_id}")
                    else:
                        logger.warning(f"Google login failed for {self.device_id}")
            
            # Jika tidak ada Google account atau login gagal, lanjutkan tanpa login
            if not self.google_login_success:
                logger.info(f"No Google login for {self.device_id}, continuing without login")
            
            # Execute task (jika driver masih aktif)
            if self.driver:
                logger.info(f"Executing task for {self.device_id}: {task_config.get('type')}")
                self._execute_task(task_config)
                self.session_start_time = time.time()
                self.is_active = True
                logger.info(f"Device {self.device_id} started successfully")
                return True
            else:
                logger.error(f"Driver not available for {self.device_id} after setup")
                return False
            
        except Exception as e:
            logger.error(f"Device {self.device_id} failed to start: {e}")
            self.is_active = False
            return False

    # ... (method-method lainnya tetap sama, pastikan semua method ada)
    
    def _save_session_cookies(self):
        """Save session cookies untuk persistence"""
        if not self.capabilities['save_session'] or not self.driver:
            return
        
        try:
            cookies = self.driver.get_cookies()
            self.profile_manager.save_cookies(self.device_id, cookies)
            logger.info(f"Saved cookies for {self.device_id}")
        except Exception as e:
            logger.warning(f"Could not save cookies for {self.device_id}: {e}")

    def _load_session_cookies(self):
        """Load session cookies untuk persistence"""
        if not self.capabilities['save_session'] or not self.driver:
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
                        logger.warning(f"Could not add cookie: {e}")
                
                # Refresh to apply cookies
                self.driver.refresh()
                logger.info(f"Loaded cookies for {self.device_id}")
                return True
        except Exception as e:
            logger.warning(f"Could not load cookies for {self.device_id}: {e}")
        
        return False

    def _check_google_logged_in(self):
        """Check if already logged in to Google"""
        if not self.driver:
            return False
            
        try:
            # Try to access Gmail
            self.driver.get("https://mail.google.com")
            time.sleep(2)
            
            # Check if we're on Gmail inbox
            if "mail.google.com" in self.driver.current_url and "accountchooser" not in self.driver.current_url:
                return True
            
            # Alternative check: Google Account page
            self.driver.get("https://myaccount.google.com")
            time.sleep(2)
            
            if "myaccount.google.com" in self.driver.current_url:
                return True
                
        except Exception as e:
            logger.warning(f"Error checking Google login status for {self.device_id}: {e}")
        
        return False

    def _login_google(self, email, password):
        """Login ke Google dengan email dan password"""
        if not self.driver:
            return False
            
        try:
            logger.info(f"Device {self.device_id} attempting Google login: {email}")
            
            self.driver.get("https://accounts.google.com/signin")
            time.sleep(3)
            
            # Input email
            email_field = WebDriverWait(self.driver, 15).until(
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
            password_field = WebDriverWait(self.driver, 15).until(
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
                logger.info(f"Google login successful for {email}")
                
                # Save session and mark as logged in
                self._save_session_cookies()
                self.profile_manager.mark_google_logged_in(self.device_id, email)
                
                return True
            else:
                logger.warning(f"Google login may have failed for {email}")
                return False
                
        except Exception as e:
            logger.error(f"Google login failed for {email}: {e}")
            return False

    def _execute_task(self, task_config):
        """Execute assigned task dengan konfigurasi scenario"""
        task_type = task_config.get('type', 'browsing')
        
        try:
            logger.info(f"Executing {task_type} task for {self.device_id}")
            
            if task_type == 'search_engine':
                self._execute_search_task(task_config)
            elif task_type == 'youtube':
                self._execute_youtube_task(task_config)
            elif task_type == 'website_visit':
                self._execute_visit_task(task_config)
            else:
                self._execute_browsing_task(task_config)
                
            logger.info(f"Task {task_type} completed for {self.device_id}")
                
        except Exception as e:
            logger.error(f"Task execution failed for {self.device_id}: {e}")

    # ... (method-method task execution tetap sama)

    def is_running(self):
        """Check if device is running"""
        if not self.is_active or not self.driver:
            return False
        
        # Check session duration
        if self.session_start_time:
            session_duration = time.time() - self.session_start_time
            if session_duration > self.capabilities['max_session_duration']:
                logger.info(f"Session duration exceeded for {self.device_id}, stopping")
                self.stop_session()
                return False
        
        return self.is_active

    def is_healthy(self):
        """Check if device session is healthy"""
        try:
            # Check if driver is still responsive
            self.driver.current_url
            return True
        except:
            logger.warning(f"Device {self.device_id} is not healthy")
            return False

    def stop_session(self):
        """Stop device session dan save state"""
        try:
            # Save session before quitting
            if self.google_login_success and self.capabilities['save_session']:
                self._save_session_cookies()
            
            if self.driver:
                self.driver.quit()
        except Exception as e:
            logger.warning(f"Error during session stop for {self.device_id}: {e}")
        
        self.driver = None
        self.is_active = False
        self.session_start_time = None
        logger.info(f"Device {self.device_id} session stopped")

    def get_status(self):
        """Get device status"""
        session_duration = 0
        if self.session_start_time:
            session_duration = time.time() - self.session_start_time
        
        return {
            'device_id': self.device_id,
            'is_active': self.is_active,
            'google_login_success': self.google_login_success,
            'current_task': self.current_task,
            'session_duration': session_duration,
            'browser_type': 'chrome'
            }
