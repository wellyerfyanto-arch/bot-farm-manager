// Global variables
let statsInterval;
let devicesInterval;
let currentScenario = null;

// Add log entry
function addLog(message, type = 'info') {
    const logContainer = document.getElementById('logContainer');
    const timestamp = new Date().toLocaleTimeString();
    
    let icon = 'ℹ️';
    if (type === 'error') icon = '❌';
    else if (type === 'success') icon = '✅';
    else if (type === 'warning') icon = '⚠️';
    
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry fade-in';
    logEntry.innerHTML = `<span class="text-muted">[${timestamp}]</span> ${icon} ${message}`;
    
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

// Show/hide scenario configuration
function showScenarioConfig() {
    // Hide all config sections first
    document.querySelectorAll('.scenario-config').forEach(el => {
        el.style.display = 'none';
    });
    
    const scenarioType = document.getElementById('scenarioType').value;
    if (scenarioType) {
        document.getElementById(scenarioType + 'Config').style.display = 'block';
        updateGoogleAccountsNotice(scenarioType);
    }
}

// Save scenario configuration
function saveScenarioConfig() {
    const scenarioType = document.getElementById('scenarioType').value;
    
    if (!scenarioType) {
        alert('Please select a scenario type first!');
        return;
    }

    let scenarioConfig = {
        type: scenarioType,
        name: document.getElementById('scenarioType').options[document.getElementById('scenarioType').selectedIndex].text,
        timestamp: new Date().toISOString()
    };

    switch (scenarioType) {
        case 'youtube':
            scenarioConfig.urls = document.getElementById('youtubeUrls').value.split('\n').filter(url => url.trim());
            scenarioConfig.minTime = parseInt(document.getElementById('youtubeMinTime').value);
            scenarioConfig.maxTime = parseInt(document.getElementById('youtubeMaxTime').value);
            scenarioConfig.autoLike = document.getElementById('youtubeLike').checked;
            scenarioConfig.autoSubscribe = document.getElementById('youtubeSubscribe').checked;
            
            if (scenarioConfig.urls.length === 0) {
                alert('Please add at least one YouTube URL!');
                return;
            }
            break;
            
        case 'traffic':
            scenarioConfig.urls = document.getElementById('trafficUrls').value.split('\n').filter(url => url.trim());
            scenarioConfig.duration = parseInt(document.getElementById('trafficDuration').value);
            scenarioConfig.pagesPerSession = parseInt(document.getElementById('trafficPages').value);
            scenarioConfig.randomClick = document.getElementById('trafficRandomClick').checked;
            scenarioConfig.randomScroll = document.getElementById('trafficScroll').checked;
            
            if (scenarioConfig.urls.length === 0) {
                alert('Please add at least one target URL!');
                return;
            }
            break;
            
        case 'search':
            scenarioConfig.engine = document.getElementById('searchEngine').value;
            scenarioConfig.keywords = document.getElementById('searchKeywords').value.split('\n').filter(kw => kw.trim());
            scenarioConfig.searchesPerDevice = parseInt(document.getElementById('searchCount').value);
            scenarioConfig.minClicks = parseInt(document.getElementById('searchMinClick').value);
            scenarioConfig.maxClicks = parseInt(document.getElementById('searchMaxClick').value);
            
            if (scenarioConfig.keywords.length === 0) {
                alert('Please add at least one search keyword!');
                return;
            }
            break;
            
        case 'custom':
            try {
                scenarioConfig.custom = JSON.parse(document.getElementById('customJson').value);
            } catch (e) {
                alert('Invalid JSON format! Please check your configuration.');
                return;
            }
            break;
    }

    // Save to localStorage and global variable
    localStorage.setItem('currentScenario', JSON.stringify(scenarioConfig));
    currentScenario = scenarioConfig;
    
    addLog(`Scenario "${scenarioConfig.name}" configuration saved`, 'success');
}

// Load scenario preset
function loadScenarioPreset() {
    const scenarioType = document.getElementById('scenarioType').value;
    
    if (!scenarioType) {
        alert('Please select a scenario type first!');
        return;
    }

    switch (scenarioType) {
        case 'youtube':
            document.getElementById('youtubeUrls').value = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ\nhttps://www.youtube.com/watch?v=JGwWNGJdvx8';
            document.getElementById('youtubeMinTime').value = '60';
            document.getElementById('youtubeMaxTime').value = '180';
            document.getElementById('youtubeLike').checked = true;
            document.getElementById('youtubeSubscribe').checked = false;
            break;
            
        case 'traffic':
            document.getElementById('trafficUrls').value = 'https://example.com\nhttps://example.com/blog\nhttps://example.com/products';
            document.getElementById('trafficDuration').value = '120';
            document.getElementById('trafficPages').value = '5';
            document.getElementById('trafficRandomClick').checked = true;
            document.getElementById('trafficScroll').checked = true;
            break;
            
        case 'search':
            document.getElementById('searchEngine').value = 'google';
            document.getElementById('searchKeywords').value = 'artificial intelligence\nmachine learning\ndeep learning\nneural networks';
            document.getElementById('searchCount').value = '10';
            document.getElementById('searchMinClick').value = '2';
            document.getElementById('searchMaxClick').value = '5';
            break;
            
        case 'custom':
            document.getElementById('customJson').value = `{
  "tasks": [
    {
      "type": "website_visit",
      "urls": ["https://example.com", "https://example.com/blog"],
      "duration": 120,
      "random_click": true
    },
    {
      "type": "search_engine", 
      "engine": "google",
      "keywords": ["technology", "innovation"],
      "max_results": 5
    }
  ]
}`;
            break;
    }
    
    addLog(`Loaded preset for ${scenarioType} scenario`, 'info');
}

// Update Google accounts requirement notice
function updateGoogleAccountsNotice(scenarioType) {
    const accountsTextarea = document.getElementById('googleAccounts');
    const label = accountsTextarea.closest('.row').querySelector('.form-label');
    
    if (scenarioType === 'youtube') {
        label.innerHTML = 'Google Accounts <span class="text-danger">*Required for YouTube*</span>';
        accountsTextarea.placeholder = 'YouTube scenario requires Google accounts!\nFormat: email:password\naccount1@gmail.com:password1\naccount2@gmail.com:password2';
    } else {
        label.innerHTML = 'Google Accounts';
        accountsTextarea.placeholder = 'Format: email:password\naccount1@gmail.com:password1\naccount2@gmail.com:password2';
    }
}

// Start bot farm
async function startFarm() {
    const scenarioConfig = JSON.parse(localStorage.getItem('currentScenario') || '{}');
    
    if (!scenarioConfig.type) {
        alert('Please configure a scenario first!');
        return;
    }

    const accountsText = document.getElementById('googleAccounts').value;
    const accounts = parseGoogleAccounts(accountsText);
    
    // Check if YouTube scenario has Google accounts
    if (scenarioConfig.type === 'youtube' && accounts.length === 0) {
        alert('YouTube scenario requires Google accounts! Please add Google accounts first.');
        return;
    }

    if (accounts.length === 0) {
        if (!confirm('No Google accounts provided. Continue without Google login?')) {
            return;
        }
    }

    const devicesConfig = generateDevicesConfig(accounts.length);
    const tasksConfig = generateTasksFromScenario(scenarioConfig, accounts);

    try {
        addLog(`Starting bot farm with ${scenarioConfig.name} scenario...`, 'info');
        
        const response = await fetch('/api/farm/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                devices: devicesConfig,
                tasks: tasksConfig
            })
        });

        const data = await response.json();
        
        if (data.status === 'success') {
            addLog(`Bot farm started successfully with ${scenarioConfig.name} scenario!`, 'success');
            startMonitoring();
        } else {
            addLog('Failed to start bot farm: ' + data.message, 'error');
        }
    } catch (error) {
        addLog('Error starting bot farm: ' + error.message, 'error');
    }
}

// Stop bot farm
async function stopFarm() {
    try {
        addLog('Stopping bot farm...', 'warning');
        const response = await fetch('/api/farm/stop');
        const data = await response.json();
        
        if (data.status === 'success') {
            addLog('Bot farm stopped successfully.', 'success');
            stopMonitoring();
        }
    } catch (error) {
        addLog('Error stopping bot farm: ' + error.message, 'error');
    }
}

// Update Google accounts
async function updateGoogleAccounts() {
    const accountsText = document.getElementById('googleAccounts').value;
    const accounts = parseGoogleAccounts(accountsText);
    
    try {
        const response = await fetch('/api/google/accounts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ accounts: accounts })
        });

        const data = await response.json();
        
        if (data.status === 'success') {
            addLog(`Updated ${accounts.length} Google accounts`, 'success');
        }
    } catch (error) {
        addLog('Error updating accounts: ' + error.message, 'error');
    }
}

// Parse Google accounts from text
function parseGoogleAccounts(text) {
    const accounts = [];
    const lines = text.split('\n');
    
    for (const line of lines) {
        const trimmedLine = line.trim();
        if (!trimmedLine) continue;
        
        const [email, password] = trimmedLine.split(':').map(s => s.trim());
        if (email && password && email.includes('@')) {
            accounts.push({ 
                email: email, 
                password: password,
                device_id: `device_${accounts.length + 1}`
            });
        }
    }
    
    return accounts;
}

// Generate devices configuration
function generateDevicesConfig(count) {
    const devices = [];
    const deviceTypes = ['desktop', 'mobile'];
    
    for (let i = 0; i < count; i++) {
        devices.push({
            id: `device_${i + 1}`,
            name: `Device ${i + 1}`,
            type: deviceTypes[i % deviceTypes.length],
            headless: false,
            proxy_enabled: true,
            max_session_duration: 3600
        });
    }
    
    // If no accounts, create at least one device
    if (devices.length === 0) {
        devices.push({
            id: 'device_1',
            name: 'Device 1',
            type: 'desktop',
            headless: false,
            proxy_enabled: true,
            max_session_duration: 3600
        });
    }
    
    return devices;
}

// Generate tasks from scenario configuration
function generateTasksFromScenario(scenarioConfig, accounts) {
    let tasks = [];
    
    switch (scenarioConfig.type) {
        case 'youtube':
            tasks = generateYouTubeTasks(scenarioConfig, accounts);
            break;
        case 'traffic':
            tasks = generateTrafficTasks(scenarioConfig, accounts);
            break;
        case 'search':
            tasks = generateSearchTasks(scenarioConfig, accounts);
            break;
        case 'custom':
            tasks = scenarioConfig.custom.tasks || [];
            break;
    }
    
    addLog(`Generated ${tasks.length} tasks for ${scenarioConfig.name} scenario`, 'info');
    return { tasks: tasks };
}

// Generate YouTube tasks
function generateYouTubeTasks(config, accounts) {
    const tasks = [];
    let taskId = 1;
    
    accounts.forEach((account, index) => {
        config.urls.forEach(url => {
            tasks.push({
                id: `task_${taskId++}`,
                type: 'youtube',
                device_id: `device_${index + 1}`,
                video_url: url,
                watch_time_min: config.minTime,
                watch_time_max: config.maxTime,
                auto_like: config.autoLike,
                auto_subscribe: config.autoSubscribe,
                priority: 'high'
            });
        });
    });
    
    return tasks;
}

// Generate traffic tasks
function generateTrafficTasks(config, accounts) {
    const tasks = [];
    let taskId = 1;
    
    accounts.forEach((account, index) => {
        tasks.push({
            id: `task_${taskId++}`,
            type: 'website_visit',
            device_id: `device_${index + 1}`,
            urls: config.urls,
            visit_duration: config.duration,
            pages_per_session: config.pagesPerSession,
            random_click: config.randomClick,
            random_scroll: config.randomScroll,
            priority: 'medium'
        });
    });
    
    return tasks;
}

// Generate search tasks
function generateSearchTasks(config, accounts) {
    const tasks = [];
    let taskId = 1;
    
    accounts.forEach((account, index) => {
        tasks.push({
            id: `task_${taskId++}`,
            type: 'search_engine',
            device_id: `device_${index + 1}`,
            engine: config.engine,
            keywords: config.keywords,
            searches_per_device: config.searchesPerDevice,
            min_result_clicks: config.minClicks,
            max_result_clicks: config.maxClicks,
            priority: 'medium'
        });
    });
    
    return tasks;
}

// Load sample accounts
function loadSampleAccounts() {
    const sampleAccounts = `example1@gmail.com:password1\nexample2@gmail.com:password2\nexample3@gmail.com:password3`;
    document.getElementById('googleAccounts').value = sampleAccounts;
    addLog('Loaded sample accounts format', 'info');
}

// Update statistics
async function updateStats() {
    try {
        const response = await fetch('/api/farm/stats');
        const data = await response.json();
        
        if (data.status === 'success') {
            displayStats(data.data);
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

// Display statistics
function displayStats(stats) {
    const statsSection = document.getElementById('statsSection');
    
    const formatTime = (seconds) => {
        if (!seconds) return '0m';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    };
    
    const statsHTML = `
        <div class="col-md-3">
            <div class="card stat-card ${stats.is_running ? 'status-online' : 'status-offline'}">
                <div class="card-body text-center">
                    <h3>${stats.is_running ? '🟢' : '🔴'}</h3>
                    <h5 class="card-title">${stats.is_running ? 'Running' : 'Stopped'}</h5>
                    <h2 class="text-primary">${formatTime(stats.uptime)}</h2>
                    <small class="text-muted">Uptime</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card stat-card">
                <div class="card-body text-center">
                    <h3>📱</h3>
                    <h5 class="card-title">Devices</h5>
                    <h2 class="text-info">${stats.active_devices || 0}/${stats.total_devices || 0}</h2>
                    <small class="text-muted">Active/Total</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card stat-card">
                <div class="card-body text-center">
                    <h3>✅</h3>
                    <h5 class="card-title">Tasks Completed</h5>
                    <h2 class="text-success">${stats.total_tasks_completed || 0}</h2>
                    <small class="text-muted">Total</small>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card stat-card">
                <div class="card-body text-center">
                    <h3>🔐</h3>
                    <h5 class="card-title">Google Logins</h5>
                    <h2 class="${(stats.google_logins_successful || 0) > 0 ? 'text-success' : 'text-warning'}">
                        ${stats.google_logins_successful || 0}/${(stats.google_logins_successful || 0) + (stats.google_logins_failed || 0)}
                    </h2>
                    <small class="text-muted">Success/Total</small>
                </div>
            </div>
        </div>
    `;
    
    statsSection.innerHTML = statsHTML;
}

// Update devices display
async function updateDevices() {
    try {
        const response = await fetch('/api/devices');
        const data = await response.json();
        
        if (data.status === 'success') {
            displayDevices(data.data);
        }
    } catch (error) {
        console.error('Error fetching devices:', error);
    }
}

// Display devices
function displayDevices(devices) {
    const devicesGrid = document.getElementById('devicesGrid');
    
    if (!devices || Object.keys(devices).length === 0) {
        devicesGrid.innerHTML = `
            <div class="col-12">
                <div class="alert alert-info text-center">
                    <i class="fas fa-info-circle me-2"></i>No devices active. Start the farm to see devices.
                </div>
            </div>
        `;
        return;
    }
    
    let devicesHTML = '';
    
    Object.entries(devices).forEach(([deviceId, device]) => {
        const statusClass = device.is_active ? 
            (device.google_login_success ? 'status-online' : 'status-working') : 
            'status-offline';
        
        const statusIcon = device.is_active ? 
            (device.google_login_success ? '🟢' : '🟡') : '🔴';
        
        const sessionDuration = device.session_duration ? Math.floor(device.session_duration / 60) : 0;
        
        devicesHTML += `
            <div class="col-md-4">
                <div class="card device-card ${statusClass}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <h6 class="card-title mb-0">
                                <i class="fas fa-mobile-alt me-2"></i>${deviceId}
                            </h6>
                            <span class="fs-5">${statusIcon}</span>
                        </div>
                        <div class="mt-2">
                            <small class="text-muted">
                                ${device.is_active ? 'Active' : 'Inactive'} • 
                                ${sessionDuration}m session
                            </small>
                        </div>
                        ${device.google_login_success ? 
                            '<span class="google-badge mt-2 d-inline-block">Google ✓</span>' : 
                            '<span class="badge bg-warning mt-2">Google ✗</span>'
                        }
                        ${device.current_task ? `
                            <div class="mt-2">
                                <small class="text-muted">Task: ${device.current_task.type}</small>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    });
    
    devicesGrid.innerHTML = devicesHTML;
}

// Start monitoring
function startMonitoring() {
    stopMonitoring(); // Clear existing intervals
    
    statsInterval = setInterval(updateStats, 3000);
    devicesInterval = setInterval(updateDevices, 5000);
    
    updateStats();
    updateDevices();
    addLog('Started real-time monitoring', 'info');
}

// Stop monitoring
function stopMonitoring() {
    if (statsInterval) clearInterval(statsInterval);
    if (devicesInterval) clearInterval(devicesInterval);
    
    statsInterval = null;
    devicesInterval = null;
}

// Load saved scenario on page load
function loadSavedScenario() {
    const savedScenario = localStorage.getItem('currentScenario');
    if (savedScenario) {
        const scenario = JSON.parse(savedScenario);
        document.getElementById('scenarioType').value = scenario.type;
        showScenarioConfig();
        addLog(`Loaded saved scenario: ${scenario.name}`, 'info');
    }
}

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    addLog('Dashboard initialized successfully');
    loadSavedScenario();
    updateStats();
    
    // Add some sample data for demo
    if (!localStorage.getItem('currentScenario')) {
        addLog('Select a scenario and configure it to get started', 'info');
    }
});
