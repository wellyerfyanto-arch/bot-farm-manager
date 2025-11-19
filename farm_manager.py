import threading
import time
import json
import logging
from datetime import datetime
from device_controller import DeviceController
from task_scheduler import TaskScheduler
from profile_manager import ProfileManager
from google_login import GoogleLoginManager

# Get logger for this module
logger = logging.getLogger(__name__)

class BotFarmManager:
    def __init__(self, config_file="config/farm_config.json"):
        logger.info("🔄 Initializing Bot Farm Manager...")
        
        self.config = self.load_config(config_file)
        self.devices = {}
        self.google_accounts = []
        self.active_sessions = 0
        self.completed_tasks = 0
        self.is_running = False
        
        try:
            # Initialize managers
            self.profile_manager = ProfileManager()
            self.task_scheduler = TaskScheduler()
            self.google_login_manager = GoogleLoginManager()
            
            # Statistics
            self.stats = {
                'total_devices': 0,
                'active_devices': 0,
                'total_tasks_completed': 0,
                'start_time': None,
                'uptime': 0,
                'google_logins_successful': 0,
                'google_logins_failed': 0
            }
            
            # Thread control
            self.farm_thread = None
            self.stats_thread = None
            
            logger.info("✅ Bot Farm Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Bot Farm Manager: {e}")
            raise

    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"📁 Loaded configuration from {config_file}")
            return config
        except FileNotFoundError:
            logger.warning(f"⚠️ Config file {config_file} not found, using defaults")
            return {
                "max_concurrent_devices": 5,
                "task_interval_min": 60,
                "task_interval_max": 300,
                "rotation_enabled": True,
                "proxy_rotation": True,
                "save_session": True
            }
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            return {
                "max_concurrent_devices": 5,
                "task_interval_min": 60,
                "task_interval_max": 300,
                "rotation_enabled": True,
                "proxy_rotation": True,
                "save_session": True
            }

    # ... (rest of the methods remain the same with proper logging)