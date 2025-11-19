import os
import time
import logging
import shutil
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from farm_manager import BotFarmManager

# Setup proper logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Get logger for this module
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Initialize farm manager
try:
    farm_manager = BotFarmManager()
    logger.info("✅ Bot Farm Manager initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize Bot Farm Manager: {e}")
    farm_manager = None

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/farm/start', methods=['POST'])
def start_farm():
    try:
        if not farm_manager:
            return jsonify({'status': 'error', 'message': 'Farm manager not initialized'})
            
        data = request.json
        devices_config = data.get('devices', [])
        tasks_config = data.get('tasks', [])
        
        if farm_manager.start_farm(devices_config, tasks_config):
            logger.info("🏁 Bot farm started successfully via API")
            return jsonify({'status': 'success', 'message': 'Bot farm started successfully'})
        else:
            logger.warning("⚠️ Failed to start bot farm via API")
            return jsonify({'status': 'error', 'message': 'Failed to start bot farm'})
    except Exception as e:
        logger.error(f"💥 Error starting farm: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/farm/stop')
def stop_farm():
    try:
        if farm_manager:
            farm_manager.stop_farm()
            logger.info("🛑 Bot farm stopped via API")
            return jsonify({'status': 'success', 'message': 'Bot farm stopped'})
        else:
            return jsonify({'status': 'error', 'message': 'Farm manager not initialized'})
    except Exception as e:
        logger.error(f"💥 Error stopping farm: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/farm/stats')
def get_farm_stats():
    try:
        if farm_manager:
            stats = farm_manager.get_farm_stats()
            return jsonify({'status': 'success', 'data': stats})
        else:
            return jsonify({'status': 'error', 'message': 'Farm manager not initialized'})
    except Exception as e:
        logger.error(f"💥 Error getting stats: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/devices')
def get_devices():
    try:
        if farm_manager:
            devices = farm_manager.get_devices_status()
            return jsonify({'status': 'success', 'data': devices})
        else:
            return jsonify({'status': 'error', 'message': 'Farm manager not initialized'})
    except Exception as e:
        logger.error(f"💥 Error getting devices: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/tasks/add', methods=['POST'])
def add_task():
    try:
        if farm_manager:
            data = request.json
            task_id = farm_manager.add_task(data)
            logger.info(f"➕ Added new task: {task_id}")
            return jsonify({'status': 'success', 'task_id': task_id})
        else:
            return jsonify({'status': 'error', 'message': 'Farm manager not initialized'})
    except Exception as e:
        logger.error(f"💥 Error adding task: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/google/accounts', methods=['POST'])
def update_google_accounts():
    try:
        if farm_manager:
            data = request.json
            accounts = data.get('accounts', [])
            farm_manager.update_google_accounts(accounts)
            logger.info(f"📧 Updated {len(accounts)} Google accounts via API")
            return jsonify({'status': 'success', 'message': 'Google accounts updated'})
        else:
            return jsonify({'status': 'error', 'message': 'Farm manager not initialized'})
    except Exception as e:
        logger.error(f"💥 Error updating Google accounts: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/scenario/save', methods=['POST'])
def save_scenario_config():
    try:
        data = request.json
        os.makedirs('config', exist_ok=True)
        with open('config/scenario_config.json', 'w') as f:
            json.dump(data, f, indent=2)
        logger.info("💾 Scenario configuration saved via API")
        return jsonify({'status': 'success', 'message': 'Scenario configuration saved'})
    except Exception as e:
        logger.error(f"💥 Error saving scenario: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/scenario/load')
def load_scenario_config():
    try:
        with open('config/scenario_config.json', 'r') as f:
            config = json.load(f)
        logger.info("📂 Scenario configuration loaded via API")
        return jsonify({'status': 'success', 'data': config})
    except FileNotFoundError:
        logger.warning("⚠️ No saved scenario found")
        return jsonify({'status': 'error', 'message': 'No saved scenario found'})
    except Exception as e:
        logger.error(f"💥 Error loading scenario: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/profiles/export/<device_id>')
def export_profile(device_id):
    try:
        if farm_manager:
            profile_data = farm_manager.profile_manager.export_profile(device_id)
            if profile_data:
                logger.info(f"📤 Exported profile for {device_id}")
                return jsonify({'status': 'success', 'data': profile_data})
            else:
                logger.warning(f"⚠️ Profile not found for {device_id}")
                return jsonify({'status': 'error', 'message': 'Profile not found'})
        else:
            return jsonify({'status': 'error', 'message': 'Farm manager not initialized'})
    except Exception as e:
        logger.error(f"💥 Error exporting profile: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/profiles/import', methods=['POST'])
def import_profile():
    try:
        if farm_manager:
            data = request.json
            device_id = data.get('device_id')
            profile_data = data.get('profile_data')
            
            if farm_manager.profile_manager.import_profile(device_id, profile_data):
                logger.info(f"📥 Imported profile for {device_id}")
                return jsonify({'status': 'success', 'message': 'Profile imported successfully'})
            else:
                logger.warning(f"⚠️ Failed to import profile for {device_id}")
                return jsonify({'status': 'error', 'message': 'Failed to import profile'})
        else:
            return jsonify({'status': 'error', 'message': 'Farm manager not initialized'})
    except Exception as e:
        logger.error(f"💥 Error importing profile: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/profiles/list')
def list_profiles():
    try:
        if farm_manager:
            profiles = farm_manager.profile_manager.get_all_profiles()
            logger.info(f"📋 Listed {len(profiles)} profiles via API")
            return jsonify({'status': 'success', 'data': profiles})
        else:
            return jsonify({'status': 'error', 'message': 'Farm manager not initialized'})
    except Exception as e:
        logger.error(f"💥 Error listing profiles: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/profiles/delete/<device_id>', methods=['DELETE'])
def delete_profile(device_id):
    try:
        profile_path = f"profiles/profile_{device_id}"
        if os.path.exists(profile_path):
            shutil.rmtree(profile_path)
            logger.info(f"🗑️ Deleted profile for {device_id}")
            return jsonify({'status': 'success', 'message': 'Profile deleted'})
        else:
            logger.warning(f"⚠️ Profile not found for deletion: {device_id}")
            return jsonify({'status': 'error', 'message': 'Profile not found'})
    except Exception as e:
        logger.error(f"💥 Error deleting profile: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'farm_manager_initialized': farm_manager is not None
    })

def create_app():
    return app

# Production configuration
if __name__ == "__main__":
    # Get port from environment (Railway provides this)
    port = int(os.environ.get('PORT', 5000))
    
    # Check if running in production
    is_production = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PRODUCTION') or port != 5000
    
    if is_production:
        # Production settings
        logger.info(f"🚀 Starting production server on port {port}")
        
        # Use Waitress as production WSGI server
        try:
            from waitress import serve
            serve(app, host='0.0.0.0', port=port)
        except ImportError:
            logger.error("❌ Waitress not available, falling back to development server")
            app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # Development settings
        logger.info(f"🔧 Starting development server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)