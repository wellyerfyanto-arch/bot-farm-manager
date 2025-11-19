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
    def __init__(self, device_id, config):
        self.device_id = device_id
        self.config = config
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
            'headless': config.get('headless', False)
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
        
        # Profile directory
        if profile and profile.get('profile_path'):
            chrome_options.add_argument(f'--user-data-dir={profile["profile_path"]}')
        
        # Anti-detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        return chrome_options

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
            if "myaccount.google.com" in self.driver.current_url or "mail.google.com" in self.driver.current_url:
                logger.info(f"✅ Google login successful for {email}")
                self.google_login_success = True
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
            
            # Login Google jika ada akun
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
            logger.error(f"❌ Task execution failed: {e}")

    def _execute_youtube_task(self, task_config):
        """Execute YouTube task dengan konfigurasi scenario"""
        if not self.google_login_success:
            logger.warning("⚠️ Skipping YouTube task - Google login required")
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
            
            logger.info(f"🎥 Watched YouTube video for {watch_time:.1f} seconds")
                
        except Exception as e:
            logger.error(f"❌ YouTube task failed: {e}")

    def _youtube_like_video(self):
        """Like YouTube video"""
        try:
            like_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='like']")
            if like_buttons:
                like_buttons[0].click()
                time.sleep(1)
                logger.info("👍 Liked YouTube video")
        except Exception as e:
            logger.warning(f"⚠️ Could not like video: {e}")

    def _youtube_subscribe(self):
        """Subscribe to YouTube channel"""
        try:
            subscribe_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='Subscribe']")
            if subscribe_buttons:
                subscribe_buttons[0].click()
                time.sleep(1)
                logger.info("🔔 Subscribed to YouTube channel")
        except Exception as e:
            logger.warning(f"⚠️ Could not subscribe: {e}")

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
                logger.info(f"🌐 Visited {url} for {duration} seconds")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to visit {url}: {e}")

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
                logger.error(f"❌ Search task failed for keyword {keyword}: {e}")

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
        
        logger.info(f"🔍 Searched Google for: {keyword}")

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
        
        logger.info(f"🔍 Searched Bing for: {keyword}")

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
            logger.warning(f"⚠️ Could not click search results: {e}")

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
            self.driver.current_url
            return True
        except:
            return False

    def restart_session(self):
        """Restart device session"""
        self.stop_session()
        time.sleep(5)
        return self.start_session(self.current_profile, self.current_task)

    def stop_session(self):
        """Stop device session"""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass
        
        self.driver = None
        self.is_active = False
        self.session_start_time = None
        logger.info(f"🛑 Device {self.device_id} session stopped")

    def get_status(self):
        """Get device status"""
        return {
            'device_id': self.device_id,
            'is_active': self.is_active,
            'google_login_success': self.google_login_success,
            'current_task': self.current_task,
            'session_duration': time.time() - self.session_start_time if self.session_start_time else 0
        }