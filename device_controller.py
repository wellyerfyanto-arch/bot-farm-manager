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
            'headless': True,  # Force headless untuk Railway
            'save_session': config.get('save_session', True)
        }

    def _setup_chrome_driver(self, profile):
        """Setup Chrome driver dengan prioritas Chrome nyata"""
        try:
            # Force menggunakan Chrome nyata, bukan SimpleBrowser
            logger.info(f"Attempting to setup real Chrome for {self.device_id}")
            
            from chrome_setup import setup_chrome_driver, check_chrome_availability
            
            # Cek Chrome availability
            if not check_chrome_availability():
                logger.error(f"Chrome not available for {self.device_id}, setup failed")
                raise RuntimeError("Chrome not available")
                
            # Setup Chrome driver
            driver = setup_chrome_driver()
            
            # Apply profile settings jika ada
            if profile and profile.get('profile_path'):
                logger.info(f"Profile path available for {self.device_id}: {profile['profile_path']}")
            
            logger.info(f"Real Chrome driver setup successful for {self.device_id}")
            return driver
            
        except Exception as e:
            logger.error(f"Real Chrome setup failed for {self.device_id}: {e}")
            
            # Jangan fallback ke SimpleBrowser - biarkan error
            logger.error(f"No fallback to SimpleBrowser for {self.device_id}. Chrome required.")
            raise RuntimeError(f"Chrome setup failed: {str(e)}")

    def start_session(self, profile, task_config):
        """Start browser session dengan login Google"""
        try:
            self.current_profile = profile
            self.current_task = task_config
            
            # Setup Chrome driver
            self.driver = self._setup_chrome_driver(profile)
            
            if self.driver is None:
                logger.error("No driver available for %s", self.device_id)
                return False
            
            # Check if already logged in via profile (cookies)
            if self.profile_manager.is_google_logged_in(self.device_id):
                logger.info("Checking existing Google session for %s", self.device_id)
                
                # Try to load cookies
                if self._load_session_cookies():
                    time.sleep(2)
                    
                # Check if still logged in
                if self._check_google_logged_in():
                    self.google_login_success = True
                    logger.info("Resumed Google session for %s", self.device_id)
                else:
                    # Session expired, need to login again
                    logger.info("Google session expired for %s", self.device_id)
                    self.google_login_success = False
            
            # Login Google jika belum login dan ada akun
            if not self.google_login_success:
                google_account = self.config.get('google_account')
                if google_account and google_account.get('email') and google_account.get('password'):
                    login_success = self._login_google(google_account['email'], google_account['password'])
                    if login_success:
                        self.google_login_success = True
            
            # Jika tidak ada Google account atau login gagal, lanjutkan tanpa login
            if not self.google_login_success:
                logger.info("No Google login for %s, continuing without login", self.device_id)
            
            # Execute task (jika driver masih aktif)
            if self.driver:
                self._execute_task(task_config)
                self.session_start_time = time.time()
                self.is_active = True
                logger.info("Device %s started successfully", self.device_id)
                return True
            else:
                logger.error("Driver not available for %s", self.device_id)
                return False
            
        except Exception as e:
            logger.error("Device %s failed to start: %s", self.device_id, e)
            self.is_active = False
            return False

    def _save_session_cookies(self):
        """Save session cookies untuk persistence"""
        if not self.capabilities['save_session'] or not self.driver:
            return
        
        try:
            cookies = self.driver.get_cookies()
            self.profile_manager.save_cookies(self.device_id, cookies)
            logger.info("Saved cookies for %s", self.device_id)
        except Exception as e:
            logger.warning("Could not save cookies for %s: %s", self.device_id, e)

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
                        logger.warning("Could not add cookie: %s", e)
                
                # Refresh to apply cookies
                self.driver.refresh()
                logger.info("Loaded cookies for %s", self.device_id)
                return True
        except Exception as e:
            logger.warning("Could not load cookies for %s: %s", self.device_id, e)
        
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
            logger.warning("Error checking Google login status: %s", e)
        
        return False

    def _login_google(self, email, password):
        """Login ke Google dengan email dan password"""
        if not self.driver:
            return False
            
        try:
            logger.info("Device %s attempting Google login: %s", self.device_id, email)
            
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
                logger.info("Google login successful for %s", email)
                
                # Save session and mark as logged in
                self._save_session_cookies()
                self.profile_manager.mark_google_logged_in(self.device_id, email)
                
                return True
            else:
                logger.warning("Google login may have failed for %s", email)
                return False
                
        except Exception as e:
            logger.error("Google login failed for %s: %s", email, e)
            return False

    def _execute_task(self, task_config):
        """Execute assigned task dengan konfigurasi scenario"""
        task_type = task_config.get('type', 'browsing')
        
        try:
            if task_type == 'search_engine':
                self._execute_search_task(task_config)
            elif task_type == 'youtube':
                self._execute_youtube_task(task_config)
            elif task_type == 'website_visit':
                self._execute_visit_task(task_config)
            else:
                self._execute_browsing_task(task_config)
                
        except Exception as e:
            logger.error("Task execution failed: %s", e)

    def _execute_youtube_task(self, task_config):
        """Execute YouTube task dengan konfigurasi scenario"""
        if not self.google_login_success:
            logger.warning("Skipping YouTube task - Google login required")
            return
            
        try:
            # Gunakan video URL dari konfigurasi jika ada
            video_url = task_config.get('video_url')
            if video_url:
                self.driver.get(video_url)
            else:
                self.driver.get("https://www.youtube.com")
            
            time.sleep(5)
            
            # Gunakan watch time dari konfigurasi
            min_time = task_config.get('watch_time_min', 30)
            max_time = task_config.get('watch_time_max', 120)
            watch_time = random.uniform(min_time, max_time)
            
            # Simulate watching behavior
            self._simulate_human_behavior()
            
            # Auto like jika diaktifkan
            if task_config.get('auto_like'):
                self._youtube_like_video()
                
            # Auto subscribe jika diaktifkan
            if task_config.get('auto_subscribe'):
                self._youtube_subscribe()
                
            # Watch for configured time
            time.sleep(watch_time)
            
            logger.info("Watched YouTube video for %.1f seconds", watch_time)
                
        except Exception as e:
            logger.error("YouTube task failed: %s", e)

    def _youtube_like_video(self):
        """Like YouTube video"""
        try:
            like_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='like']")
            if like_buttons:
                like_buttons[0].click()
                time.sleep(1)
                logger.info("Liked YouTube video")
        except Exception as e:
            logger.warning("Could not like video: %s", e)

    def _youtube_subscribe(self):
        """Subscribe to YouTube channel"""
        try:
            subscribe_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Subscribe']")
            if subscribe_buttons:
                subscribe_buttons[0].click()
                time.sleep(1)
                logger.info("Subscribed to YouTube channel")
        except Exception as e:
            logger.warning("Could not subscribe: %s", e)

    def _execute_visit_task(self, task_config):
        """Execute website visit task dengan konfigurasi"""
        urls = task_config.get('urls', [])
        duration = task_config.get('visit_duration', 30)
        pages_per_session = task_config.get('pages_per_session', 3)
        random_click = task_config.get('random_click', True)
        random_scroll = task_config.get('random_scroll', True)
        
        # Pilih subset URL acak
        selected_urls = random.sample(urls, min(pages_per_session, len(urls)))
        
        for url in selected_urls:
            try:
                self.driver.get(url)
                
                if random_scroll:
                    self._simulate_human_behavior()
                    
                if random_click:
                    self._click_random_links()
                    
                time.sleep(duration)
                logger.info("Visited %s for %d seconds", url, duration)
                
            except Exception as e:
                logger.warning("Failed to visit %s: %s", url, e)

    def _execute_search_task(self, task_config):
        """Execute search engine task dengan konfigurasi"""
        search_engine = task_config.get('engine', 'google')
        keywords = task_config.get('keywords', ['technology'])
        searches_per_device = task_config.get('searches_per_device', 5)
        min_clicks = task_config.get('min_result_clicks', 1)
        max_clicks = task_config.get('max_result_clicks', 3)
        
        # Pilih keyword acak
        selected_keywords = random.choices(keywords, k=searches_per_device)
        
        for keyword in selected_keywords:
            try:
                if search_engine in ['google', 'both']:
                    self._execute_google_search(keyword, min_clicks, max_clicks)
                    
                if search_engine in ['bing', 'both']:
                    self._execute_bing_search(keyword, min_clicks, max_clicks)
                    
            except Exception as e:
                logger.error("Search task failed for keyword %s: %s", keyword, e)

    def _execute_google_search(self, keyword, min_clicks, max_clicks):
        """Execute Google search"""
        self.driver.get("https://www.google.com")
        time.sleep(random.uniform(3, 8))
        
        # Input keyword
        search_box = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "q"))
        )
        search_box.clear()
        
        # Type like human
        for char in keyword:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        
        search_box.submit()
        time.sleep(random.uniform(3, 8))
        
        # Click random results
        self._click_search_results(min_clicks, max_clicks)
        
        logger.info("Searched Google for: %s", keyword)

    def _execute_bing_search(self, keyword, min_clicks, max_clicks):
        """Execute Bing search"""
        self.driver.get("https://www.bing.com")
        time.sleep(random.uniform(3, 8))
        
        # Input keyword
        search_box = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "q"))
        )
        search_box.clear()
        
        for char in keyword:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        
        search_box.submit()
        time.sleep(random.uniform(3, 8))
        
        # Click random results
        self._click_search_results(min_clicks, max_clicks)
        
        logger.info("Searched Bing for: %s", keyword)

    def _click_search_results(self, min_clicks, max_clicks):
        """Click random search results"""
        try:
            # Find search result links (avoid ads)
            results = self.driver.find_elements(By.CSS_SELECTOR, "h3")
            valid_results = [r for r in results if r.is_displayed()]
            
            num_clicks = random.randint(min_clicks, max_clicks)
            
            for i in range(min(num_clicks, len(valid_results))):
                try:
                    valid_results[i].click()
                    time.sleep(random.uniform(5, 15))
                    self.driver.back()
                    time.sleep(2)
                except:
                    continue
                    
        except Exception as e:
            logger.warning("Could not click search results: %s", e)

    def _execute_browsing_task(self, task_config):
        """Execute general browsing task"""
        self._simulate_human_browsing()

    def _simulate_human_behavior(self):
        """Simulate human-like behavior"""
        try:
            # Random scrolling
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            for _ in range(random.randint(2, 5)):
                scroll_pos = random.randint(100, scroll_height // 2)
                self.driver.execute_script(f"window.scrollTo(0, {scroll_pos});")
                time.sleep(random.uniform(1, 3))
        except:
            pass

    def _simulate_human_browsing(self):
        """Simulate realistic browsing patterns"""
        behaviors = [self._random_scrolling, self._click_random_links]
        
        for _ in range(random.randint(3, 6)):
            behavior = random.choice(behaviors)
            try:
                behavior()
                time.sleep(random.uniform(5, 15))
            except:
                continue

    def _random_scrolling(self):
        """Random scrolling behavior"""
        scroll_height = self.driver.execute_script("return document.body.scrollHeight")
        current_pos = 0
        
        for _ in range(random.randint(3, 8)):
            scroll_amount = random.randint(100, 400)
            current_pos = min(scroll_height, current_pos + scroll_amount)
            self.driver.execute_script(f"window.scrollTo(0, {current_pos});")
            time.sleep(random.uniform(0.5, 2))

    def _click_random_links(self):
        """Click random links on page"""
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            valid_links = [link for link in links if link.is_displayed() and link.is_enabled()]
            
            if valid_links:
                random.choice(valid_links[:5]).click()
                time.sleep(random.uniform(3, 8))
        except:
            pass

    def is_running(self):
        """Check if device is running"""
        if not self.is_active or not self.driver:
            return False
        
        # Check session duration
        if self.session_start_time:
            session_duration = time.time() - self.session_start_time
            if session_duration > self.capabilities['max_session_duration']:
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
            return False

    def restart_session(self):
        """Restart device session"""
        logger.info("Restarting session for %s", self.device_id)
        self.stop_session()
        time.sleep(5)
        return self.start_session(self.current_profile, self.current_task)

    def stop_session(self):
        """Stop device session dan save state"""
        try:
            # Save session before quitting
            if self.google_login_success and self.capabilities['save_session']:
                self._save_session_cookies()
            
            if self.driver:
                self.driver.quit()
        except Exception as e:
            logger.warning("Error during session stop: %s", e)
        
        self.driver = None
        self.is_active = False
        self.session_start_time = None
        logger.info("Device %s session stopped", self.device_id)

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