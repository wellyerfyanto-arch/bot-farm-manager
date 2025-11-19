import threading
import time
import json
import logging
from datetime import datetime

# Get logger for this module
logger = logging.getLogger(__name__)

class BotFarmManager:
    def __init__(self, config_file="config/farm_config.json"):
        logger.info("Initializing Bot Farm Manager...")
        
        self.config = self.load_config(config_file)
        self.devices = {}
        self.google_accounts = []
        self.active_sessions = 0
        self.completed_tasks = 0
        self.is_running = False
        
        try:
            # Import managers here to avoid circular imports
            from task_scheduler import TaskScheduler
            from profile_manager import ProfileManager
            from google_login import GoogleLoginManager
            
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
            
            logger.info("Bot Farm Manager initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Bot Farm Manager: %s", e)
            # Set managers to None but don't raise to allow app to start
            self.profile_manager = None
            self.task_scheduler = None
            self.google_login_manager = None

    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info("Loaded configuration from %s", config_file)
            return config
        except FileNotFoundError:
            logger.warning("Config file %s not found, using defaults", config_file)
            return {
                "max_concurrent_devices": 2,
                "task_interval_min": 180,
                "task_interval_max": 600,
                "rotation_enabled": True,
                "proxy_rotation": False,
                "headless": True,
                "save_session": True
            }
        except Exception as e:
            logger.error("Error loading config: %s", e)
            return {
                "max_concurrent_devices": 2,
                "task_interval_min": 180,
                "task_interval_max": 600,
                "rotation_enabled": True,
                "proxy_rotation": False,
                "headless": True,
                "save_session": True
            }

    def update_google_accounts(self, accounts):
        """Update Google accounts list"""
        self.google_accounts = accounts
        logger.info("Updated Google accounts: %d accounts", len(accounts))

    def initialize_devices(self, devices_config):
        """Initialize devices from configuration"""
        if not self.profile_manager:
            logger.error("Profile manager not initialized")
            return
            
        self.devices.clear()
        
        for i, device_config in enumerate(devices_config):
            device_id = f"device_{i+1}"
            
            # Assign Google account if available
            if i < len(self.google_accounts):
                device_config['google_account'] = self.google_accounts[i]
            else:
                device_config['google_account'] = None
            
            try:
                from device_controller import DeviceController
                # Pass profile_manager to device controller
                self.devices[device_id] = DeviceController(device_id, device_config, self.profile_manager)
                logger.info("Device %s initialized", device_id)
            except Exception as e:
                logger.error("Failed to initialize device %s: %s", device_id, e)
        
        self.stats['total_devices'] = len(self.devices)
        logger.info("Total devices initialized: %d", len(self.devices))

    def start_device(self, device_id, task_config):
        """Start a single device with specific task"""
        try:
            device = self.devices[device_id]
            
            # Generate unique profile
            profile = self.profile_manager.create_profile(device_id)
            
            # Start device session
            if device.start_session(profile, task_config):
                self.active_sessions += 1
                self.stats['active_devices'] = self.active_sessions
                
                # Monitor device
                monitor_thread = threading.Thread(
                    target=self.monitor_device, 
                    args=(device_id,)
                )
                monitor_thread.daemon = True
                monitor_thread.start()
                
                logger.info("Device %s started successfully", device_id)
                return True
                
        except Exception as e:
            logger.error("Error starting device %s: %s", device_id, e)
        
        return False

    def monitor_device(self, device_id):
        """Monitor device execution"""
        device = self.devices[device_id]
        
        while device.is_running() and self.is_running:
            time.sleep(10)
            
            if not device.is_healthy():
                logger.warning("Device %s not healthy, restarting...", device_id)
                device.restart_session()
        
        # Device completed
        if device_id in self.devices:
            self.active_sessions -= 1
            self.completed_tasks += 1
            self.stats['active_devices'] = self.active_sessions
            self.stats['total_tasks_completed'] = self.completed_tasks
            
            # Update Google login stats
            if device.google_login_success:
                self.stats['google_logins_successful'] += 1
            else:
                self.stats['google_logins_failed'] += 1
            
            logger.info("Device %s completed task", device_id)

    def start_farm(self, devices_config, tasks_config):
        """Start the entire bot farm"""
        if self.is_running:
            logger.warning("Farm is already running")
            return False

        try:
            self.is_running = True
            self.stats['start_time'] = datetime.now()
            
            # Initialize devices and tasks
            self.initialize_devices(devices_config)
            
            if self.task_scheduler:
                self.task_scheduler.load_tasks_config(tasks_config)
            
            # Start farm loop
            self.farm_thread = threading.Thread(target=self._farm_loop)
            self.farm_thread.daemon = True
            self.farm_thread.start()
            
            # Start stats monitor
            self.stats_thread = threading.Thread(target=self._stats_monitor)
            self.stats_thread.daemon = True
            self.stats_thread.start()
            
            logger.info("Bot Farm started successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to start farm: %s", e)
            self.is_running = False
            return False

    def _farm_loop(self):
        """Main farm loop dengan device-task mapping"""
        while self.is_running:
            try:
                # Use is_active for simplicity in Railway environment
                available_devices = [
                    device_id for device_id, device in self.devices.items()
                    if not device.is_active
                ]
                
                if self.task_scheduler:
                    pending_tasks = self.task_scheduler.get_pending_tasks()
                else:
                    pending_tasks = []
                
                # Simple task assignment
                for i, task in enumerate(pending_tasks[:len(available_devices)]):
                    if i < len(available_devices):
                        device_id = available_devices[i]
                        if self.start_device(device_id, task):
                            if self.task_scheduler:
                                self.task_scheduler.mark_task_assigned(task['id'])
                
                time.sleep(10)  # Longer sleep for Railway environment
                
            except Exception as e:
                logger.error("Error in farm loop: %s", e)
                time.sleep(30)  # Even longer sleep on error

    def _stats_monitor(self):
        """Monitor and log statistics"""
        while self.is_running:
            try:
                current_time = datetime.now()
                if self.stats['start_time']:
                    self.stats['uptime'] = (current_time - self.stats['start_time']).total_seconds()
                
                time.sleep(30)
                
            except Exception as e:
                logger.error("Error in stats monitor: %s", e)
                time.sleep(30)

    def stop_farm(self):
        """Stop the bot farm"""
        if not self.is_running:
            logger.info("Farm is not running")
            return
            
        self.is_running = False
        logger.info("Stopping Bot Farm...")
        
        # Stop all devices
        for device_id, device in self.devices.items():
            try:
                device.stop_session()
            except Exception as e:
                logger.error("Error stopping device %s: %s", device_id, e)
        
        self.active_sessions = 0
        self.stats['active_devices'] = 0
        logger.info("Bot Farm stopped")

    def get_farm_stats(self):
        """Get current farm statistics"""
        if self.stats['start_time']:
            self.stats['uptime'] = (datetime.now() - self.stats['start_time']).total_seconds()
        
        return {
            **self.stats,
            'is_running': self.is_running,
            'active_sessions': self.active_sessions,
            'completed_tasks': self.completed_tasks,
            'total_google_accounts': len(self.google_accounts)
        }

    def get_devices_status(self):
        """Get status of all devices"""
        devices_status = {}
        for device_id, device in self.devices.items():
            try:
                devices_status[device_id] = device.get_status()
            except Exception as e:
                logger.error("Error getting status for %s: %s", device_id, e)
                devices_status[device_id] = {
                    'device_id': device_id,
                    'is_active': False,
                    'google_login_success': False,
                    'current_task': None,
                    'session_duration': 0
                }
        return devices_status

    def add_task(self, task_config):
        """Add new task to scheduler"""
        try:
            if self.task_scheduler:
                task_id = self.task_scheduler.add_task(task_config)
                logger.info("Added new task: %s", task_id)
                return task_id
            else:
                logger.error("Task scheduler not initialized")
                return None
        except Exception as e:
            logger.error("Error adding task: %s", e)
            return None
