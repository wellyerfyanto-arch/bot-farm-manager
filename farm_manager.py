import threading
import time
import json
import logging
from datetime import datetime
from device_controller import DeviceController
from task_scheduler import TaskScheduler
from profile_manager import ProfileManager
from google_login import GoogleLoginManager

logger = logging.getLogger(__name__)

class BotFarmManager:
    def __init__(self, config_file="config/farm_config.json"):
        self.config = self.load_config(config_file)
        self.devices = {}
        self.google_accounts = []
        self.active_sessions = 0
        self.completed_tasks = 0
        self.is_running = False
        
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

    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "max_concurrent_devices": 10,
                "task_interval_min": 30,
                "task_interval_max": 120,
                "rotation_enabled": True,
                "proxy_rotation": True
            }

    def update_google_accounts(self, accounts):
        """Update Google accounts list"""
        self.google_accounts = accounts
        logger.info(f"📧 Updated Google accounts: {len(accounts)} accounts")

    def initialize_devices(self, devices_config):
        """Initialize devices from configuration"""
        self.devices.clear()
        
        for i, device_config in enumerate(devices_config):
            device_id = f"device_{i+1}"
            
            # Assign Google account if available
            if i < len(self.google_accounts):
                device_config['google_account'] = self.google_accounts[i]
            else:
                device_config['google_account'] = None
            
            self.devices[device_id] = DeviceController(device_id, device_config)
            logger.info(f"✅ Device {device_id} initialized")
        
        self.stats['total_devices'] = len(self.devices)
        logger.info(f"🎯 Total devices initialized: {len(self.devices)}")

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
                
                logger.info(f"🚀 Device {device_id} started successfully")
                return True
                
        except Exception as e:
            logger.error(f"💥 Error starting device {device_id}: {e}")
        
        return False

    def monitor_device(self, device_id):
        """Monitor device execution"""
        device = self.devices[device_id]
        
        while device.is_running() and self.is_running:
            time.sleep(10)
            
            if not device.is_healthy():
                logger.warning(f"⚠️ Device {device_id} not healthy, restarting...")
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
            
            logger.info(f"✅ Device {device_id} completed task")

    def start_farm(self, devices_config, tasks_config):
        """Start the entire bot farm"""
        if self.is_running:
            return False

        try:
            self.is_running = True
            self.stats['start_time'] = datetime.now()
            
            # Initialize devices and tasks
            self.initialize_devices(devices_config)
            self.task_scheduler.load_tasks_config(tasks_config)
            
            # Start farm loop
            self.farm_thread = threading.Thread(target=self._farm_loop)
            self.farm_thread.daemon = True
            self.farm_thread.start()
            
            # Start stats monitor
            self.stats_thread = threading.Thread(target=self._stats_monitor)
            self.stats_thread.daemon = True
            self.stats_thread.start()
            
            logger.info("🏁 Bot Farm started successfully")
            return True
            
        except Exception as e:
            logger.error(f"💥 Failed to start farm: {e}")
            self.is_running = False
            return False

    def _farm_loop(self):
        """Main farm loop dengan device-task mapping"""
        while self.is_running:
            try:
                available_devices = [
                    device_id for device_id, device in self.devices.items()
                    if not device.is_running()
                ]
                
                pending_tasks = self.task_scheduler.get_pending_tasks()
                
                for task in pending_tasks:
                    # Cari device yang tersedia untuk task ini
                    target_device = task.get('device_id')
                    if target_device and target_device in available_devices:
                        if self.start_device(target_device, task):
                            self.task_scheduler.mark_task_assigned(task['id'])
                            available_devices.remove(target_device)
                    elif available_devices:
                        # Assign ke device mana saja yang tersedia
                        device_id = available_devices.pop(0)
                        if self.start_device(device_id, task):
                            self.task_scheduler.mark_task_assigned(task['id'])
                
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"💥 Error in farm loop: {e}")
                time.sleep(10)

    def _stats_monitor(self):
        """Monitor and log statistics"""
        while self.is_running:
            try:
                current_time = datetime.now()
                if self.stats['start_time']:
                    self.stats['uptime'] = (current_time - self.stats['start_time']).total_seconds()
                
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"💥 Error in stats monitor: {e}")
                time.sleep(30)

    def stop_farm(self):
        """Stop the bot farm"""
        self.is_running = False
        logger.info("🛑 Stopping Bot Farm...")
        
        for device in self.devices.values():
            device.stop_session()
        
        self.active_sessions = 0
        self.stats['active_devices'] = 0
        logger.info("✅ Bot Farm stopped")

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
            devices_status[device_id] = device.get_status()
        return devices_status

    def add_task(self, task_config):
        """Add new task to scheduler"""
        return self.task_scheduler.add_task(task_config)