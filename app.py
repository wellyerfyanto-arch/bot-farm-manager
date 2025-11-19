import os
import time
import logging
import shutil
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from farm_manager import BotFarmManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)
farm_manager = BotFarmManager()

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/farm/start', methods=['POST'])
def start_farm():
    try:
        data = request.json
        devices_config = data.get('devices', [])
        tasks_config = data.get('tasks', [])
        
        if farm_manager.start_farm(devices_config, tasks_config):
            return jsonify({'status': 'success', 'message': 'Bot farm started successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to start bot farm'})
    except Exception as e:
        logger.error(f"Error starting farm: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/farm/stop')
def stop_farm():
    try:
        farm_manager.stop_farm()
        return jsonify({'status': 'success', 'message': 'Bot farm stopped'})
    except Exception as e:
        logger.error(f"Error stopping farm: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/farm/stats')
def get_farm_stats():
    try:
        stats = farm_manager.get_farm_stats()
        return jsonify({'status': 'success', 'data': stats})
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/devices')
def get_devices():
    try:
        devices = farm_manager.get_devices_status()
        return jsonify({'status': 'success', 'data': devices})
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/tasks/add', methods=['POST'])
def add_task():
    try:
        data = request.json
        task_id = farm_manager.add_task(data)
        return jsonify({'status': 'success', 'task_id': task_id})
    except Exception as e:
        logger.error(f"Error adding task: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/google/accounts', methods=['POST'])
def update_google_accounts():
    try:
        data = request.json
        accounts = data.get('accounts', [])
        farm_manager.update_google_accounts(accounts)
        return jsonify({'status': 'success', 'message': 'Google accounts updated'})
    except Exception as e:
        logger.error(f"Error updating Google accounts: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/scenario/save', methods=['POST'])
def save_scenario_config():
    try:
        data = request.json
        # Simpan scenario config ke file
        os.makedirs('config', exist_ok=True)
        with open('config/scenario_config.json', 'w') as f:
            json.dump(data, f, indent=2)
        return jsonify({'status': 'success', 'message': 'Scenario configuration saved'})
    except Exception as e:
        logger.error(f"Error saving scenario: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/scenario/load')
def load_scenario_config():
    try:
        with open('config/scenario_config.json', 'r') as f:
            config = json.load(f)
        return jsonify({'status': 'success', 'data': config})
    except FileNotFoundError:
        return jsonify({'status': 'error', 'message': 'No saved scenario found'})

@app.route('/api/profiles/export/<device_id>')
def export_profile(device_id):
    try:
        profile_data = farm_manager.profile_manager.export_profile(device_id)
        if profile_data:
            return jsonify({'status': 'success', 'data': profile_data})
        else:
            return jsonify({'status': 'error', 'message': 'Profile not found'})
    except Exception as e:
        logger.error(f"Error exporting profile: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/profiles/import', methods=['POST'])
def import_profile():
    try:
        data = request.json
        device_id = data.get('device_id')
        profile_data = data.get('profile_data')
        
        if farm_manager.profile_manager.import_profile(device_id, profile_data):
            return jsonify({'status': 'success', 'message': 'Profile imported successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to import profile'})
    except Exception as e:
        logger.error(f"Error importing profile: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/profiles/list')
def list_profiles():
    try:
        profiles = farm_manager.profile_manager.get_all_profiles()
        return jsonify({'status': 'success', 'data': profiles})
    except Exception as e:
        logger.error(f"Error listing profiles: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/profiles/delete/<device_id>', methods=['DELETE'])
def delete_profile(device_id):
    try:
        profile_path = f"profiles/profile_{device_id}"
        if os.path.exists(profile_path):
            shutil.rmtree(profile_path)
            return jsonify({'status': 'success', 'message': 'Profile deleted'})
        else:
            return jsonify({'status': 'error', 'message': 'Profile not found'})
    except Exception as e:
        logger.error(f"Error deleting profile: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    
    # Auto-detect environment
    if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PYTHON_ENV') == 'production':
        # Production: Use Waitress
        from waitress import serve
        logger.info(f"🚀 Production server starting on port {port}")
        serve(app, host='0.0.0.0', port=port)
    else:
        # Development: Use Flask dev server
        logger.info(f"🔧 Development server starting on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
