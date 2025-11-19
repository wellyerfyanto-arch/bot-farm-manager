[file name]: device_controller.py
[file content begin]
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

    def _execute_search_task(self, task_config):
        """Execute search engine simulation task"""
        try:
            engine = task_config.get('engine', 'google')
            keywords = task_config.get('keywords', [])
            searches_per_device = task_config.get('searches_per_device', 10)
            min_clicks = task_config.get('min_result_clicks', 2)
            max_clicks = task_config.get('max_result_clicks', 5)
            
            logger.info(f"Starting search task on {engine} with {len(keywords)} keywords")
            
            for search_idx in range(searches_per_device):
                if not self.is_active:
                    break
                    
                # Select random keyword
                keyword = random.choice(keywords) if keywords else "test search"
                
                # Perform search
                if engine == 'google':
                    self._google_search(keyword)
                elif engine == 'bing':
                    self._bing_search(keyword)
                elif engine == 'both':
                    # Alternate between Google and Bing
                    if search_idx % 2 == 0:
                        self._google_search(keyword)
                    else:
                        self._bing_search(keyword)
                
                # Random clicks on search results
                num_clicks = random.randint(min_clicks, max_clicks)
                self._click_search_results(num_clicks)
                
                # Random delay between searches
                time.sleep(random.uniform(10, 30))
                
        except Exception as e:
            logger.error(f"Search task failed: {e}")
            raise

    def _execute_youtube_task(self, task_config):
        """Execute YouTube view farming task"""
        try:
            video_urls = task_config.get('video_urls', [])
            if isinstance(video_urls, str):
                video_urls = [video_urls]
                
            watch_time_min = task_config.get('watch_time_min', 60)
            watch_time_max = task_config.get('watch_time_max', 180)
            auto_like = task_config.get('auto_like', False)
            auto_subscribe = task_config.get('auto_subscribe', False)
            
            logger.info(f"Starting YouTube task with {len(video_urls)} videos")
            
            for video_url in video_urls:
                if not self.is_active:
                    break
                    
                try:
                    # Navigate to video
                    self.driver.get(video_url)
                    time.sleep(5)
                    
                    # Play video
                    self._click_play_button()
                    
                    # Watch for random duration
                    watch_time = random.randint(watch_time_min, watch_time_max)
                    logger.info(f"Watching video for {watch_time} seconds")
                    
                    # Simulate watching with occasional interactions
                    start_time = time.time()
                    while time.time() - start_time < watch_time and self.is_active:
                        # Random scroll
                        if random.random() < 0.3:  # 30% chance
                            self._random_scroll()
                        
                        # Random pause/play
                        if random.random() < 0.1:  # 10% chance
                            self._toggle_play_pause()
                            
                        time.sleep(10)  # Check every 10 seconds
                    
                    # Auto like if enabled
                    if auto_like:
                        self._like_video()
                    
                    # Auto subscribe if enabled
                    if auto_subscribe:
                        self._subscribe_channel()
                        
                    # Random delay before next video
                    time.sleep(random.uniform(5, 15))
                    
                except Exception as e:
                    logger.warning(f"Failed to process video {video_url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"YouTube task failed: {e}")
            raise

    def _execute_visit_task(self, task_config):
        """Execute website traffic generation task"""
        try:
            urls = task_config.get('urls', [])
            if isinstance(urls, str):
                urls = [urls]
                
            visit_duration = task_config.get('visit_duration', 120)
            pages_per_session = task_config.get('pages_per_session', 5)
            random_click = task_config.get('random_click', True)
            random_scroll = task_config.get('random_scroll', True)
            
            logger.info(f"Starting visit task with {len(urls)} URLs")
            
            for i in range(min(pages_per_session, len(urls))):
                if not self.is_active:
                    break
                    
                url = urls[i % len(urls)]  # Cycle through URLs
                
                try:
                    # Visit page
                    self.driver.get(url)
                    time.sleep(3)
                    
                    # Random scroll during visit
                    if random_scroll:
                        scroll_duration = min(visit_duration // len(urls), 30)
                        self._simulate_browsing(scroll_duration, random_click)
                    else:
                        time.sleep(5)  # Minimum stay
                        
                    # Random click if enabled
                    if random_click and random.random() < 0.7:  # 70% chance
                        self._click_random_link()
                        
                except Exception as e:
                    logger.warning(f"Failed to visit {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Visit task failed: {e}")
            raise

    def _execute_browsing_task(self, task_config):
        """Execute general browsing task"""
        try:
            logger.info("Starting general browsing task")
            
            # Default browsing behavior
            duration = task_config.get('duration', 60)
            self._simulate_browsing(duration, True)
            
        except Exception as e:
            logger.error(f"Browsing task failed: {e}")
            raise

    def _google_search(self, keyword):
        """Perform Google search"""
        try:
            self.driver.get("https://www.google.com")
            time.sleep(2)
            
            search_box = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "q"))
            )
            
            # Type search query
            search_box.clear()
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
                
            search_box.submit()
            time.sleep(3)
            
        except Exception as e:
            logger.warning(f"Google search failed: {e}")

    def _bing_search(self, keyword):
        """Perform Bing search"""
        try:
            self.driver.get("https://www.bing.com")
            time.sleep(2)
            
            search_box = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "q"))
            )
            
            # Type search query
            search_box.clear()
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
                
            search_box.submit()
            time.sleep(3)
            
        except Exception as e:
            logger.warning(f"Bing search failed: {e}")

    def _click_search_results(self, num_clicks):
        """Click on search results"""
        try:
            # Find search result links
            results = self.driver.find_elements(By.CSS_SELECTOR, "h3")
            clickable_results = []
            
            for result in results:
                try:
                    link = result.find_element(By.XPATH, "./..")
                    if link.get_attribute("href"):
                        clickable_results.append(link)
                except:
                    continue
            
            # Click random results
            for _ in range(min(num_clicks, len(clickable_results))):
                if not self.is_active:
                    break
                    
                result = random.choice(clickable_results)
                try:
                    result.click()
                    time.sleep(random.uniform(5, 15))  # Stay on page
                    self.driver.back()  # Go back to search results
                    time.sleep(2)
                except Exception as e:
                    logger.warning(f"Failed to click search result: {e}")
                    
        except Exception as e:
            logger.warning(f"Click search results failed: {e}")

    def _click_play_button(self):
        """Click YouTube play button"""
        try:
            # Try different selectors for play button
            selectors = [
                "button.ytp-play-button",
                ".ytp-large-play-button",
                "button[aria-label*='Play']"
            ]
            
            for selector in selectors:
                try:
                    play_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    play_button.click()
                    time.sleep(2)
                    return True
                except:
                    continue
                    
            return False
        except Exception as e:
            logger.warning(f"Click play button failed: {e}")
            return False

    def _random_scroll(self):
        """Perform random scrolling"""
        try:
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_pos = random.randint(100, scroll_height - 500)
            self.driver.execute_script(f"window.scrollTo(0, {scroll_pos});")
            time.sleep(random.uniform(1, 3))
        except:
            pass

    def _toggle_play_pause(self):
        """Toggle YouTube play/pause"""
        try:
            play_button = self.driver.find_element(By.CSS_SELECTOR, "button.ytp-play-button")
            play_button.click()
            time.sleep(1)
        except:
            pass

    def _like_video(self):
        """Like YouTube video"""
        try:
            like_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label*='like this video']")
            like_button.click()
            time.sleep(1)
        except:
            pass

    def _subscribe_channel(self):
        """Subscribe to YouTube channel"""
        try:
            subscribe_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Subscribe']")
            if "subscribed" not in subscribe_button.get_attribute("innerHTML"):
                subscribe_button.click()
                time.sleep(1)
        except:
            pass

    def _simulate_browsing(self, duration, random_click=False):
        """Simulate natural browsing behavior"""
        start_time = time.time()
        
        while time.time() - start_time < duration and self.is_active:
            # Random scroll
            self._random_scroll()
            
            # Random click if enabled
            if random_click and random.random() < 0.2:  # 20% chance
                self._click_random_link()
                time.sleep(random.uniform(5, 15))
                self.driver.back()
                time.sleep(2)
            
            time.sleep(random.uniform(3, 8))

    def _click_random_link(self):
        """Click random link on page"""
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            valid_links = []
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href and "http" in href and "youtube.com" not in href:
                        valid_links.append(link)
                except:
                    continue
            
            if valid_links:
                link = random.choice(valid_links)
                link.click()
                return True
                
        except Exception as e:
            logger.warning(f"Click random link failed: {e}")
            
        return False

    def restart_session(self):
        """Restart device session"""
        try:
            self.stop_session()
            time.sleep(2)
            return self.start_session(self.current_profile, self.current_task)
        except Exception as e:
            logger.error(f"Failed to restart session for {self.device_id}: {e}")
            return False

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
[file content end]