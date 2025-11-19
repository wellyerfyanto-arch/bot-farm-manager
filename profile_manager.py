import os
import json
import time
import logging

logger = logging.getLogger(__name__)

class ProfileManager:
    def __init__(self, profiles_dir="profiles"):
        self.profiles_dir = profiles_dir
        os.makedirs(profiles_dir, exist_ok=True)
    
    def create_profile(self, device_id):
        """Create browser profile for device"""
        profile_path = os.path.join(self.profiles_dir, f"profile_{device_id}")
        os.makedirs(profile_path, exist_ok=True)
        
        profile = {
            'profile_path': profile_path,
            'device_id': device_id,
            'created_at': time.time()
        }
        
        # Save profile info
        with open(os.path.join(profile_path, 'profile_info.json'), 'w') as f:
            json.dump(profile, f)
        
        logger.info(f"👤 Created profile for {device_id}")
        return profile