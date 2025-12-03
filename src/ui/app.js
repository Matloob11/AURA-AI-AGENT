const { ipcRenderer } = require('electron');
const io = require('socket.io-client');
const axios = require('axios');

const API_URL = 'http://localhost:8000';
let socket;
let isVoiceActive = false;
let isWakeWordActive = false;

// DOM Elements
const systemLogs = document.getElementById('system-logs');
const taskHistory = document.getElementById('task-history');
const responseDisplay = document.getElementById('response-display');
const userInput = document.getElementById('user-input');
const auraStatus = document.getElementById('aura-status');
const connectionStatus = document.getElementById('connection-status');

// Window Controls
document.getElementById('minimize-btn').addEventListener('click', () => {
    ipcRenderer.send('minimize-window');
});

document.getElementById('maximize-btn').addEventListener('click', () => {
    ipcRenderer.send('maximize-window');
});

document.getElementById('close-btn').addEventListener('click', () => {
    ipcRenderer.send('close-window');
});

// Initialize Socket.IO
function initSocket() {
    socket = io(API_URL);

    socket.on('connect', () => {
        addLog('✓ Connected to AURA backend');
        connectionStatus.style.color = '#00ff00';
        updateAuraStatus('CONNECTED');
        loadSystemStatus();
    });

    socket.on('disconnect', () => {
        addLog('✗ Disconnected from backend');
        connectionStatus.style.color = '#ff0000';
        updateAuraStatus('DISCONNECTED');
    });

    socket.on('event', (data) => {
        addLog(`⚡ ${data.message}`);
    });

    socket.on('ai_response', (data) => {
        displayResponse(data.message);
        addTask('AI Response', data.message.substring(0, 50) + '...');
    });

    socket.on('voice_result', (data) => {
        addLog(`🎤 Voice: ${data.text}`);
        userInput.value = data.text;
    });

    socket.on('vision_result', (data) => {
        if (data.analysis) {
            addLog(`👁️ Vision: ${data.analysis.substring(0, 50)}...`);
            displayResponse(data.analysis);
        }
    });

    socket.on('automation_result', (data) => {
        addLog(`⚙️ Automation: ${data.action} completed`);
        addTask('Automation', data.action);
    });
}

// Load System Status
async function loadSystemStatus() {
    try {
        const response = await axios.get(`${API_URL}/status`);
        const status = response.data;

        // Update engine status
        updateEngineStatus('ai-status', status.services.ai_engine);
        updateEngineStatus('voice-status-info', status.services.voice_engine);
        updateEngineStatus('vision-status-info', status.services.vision_engine);
        updateEngineStatus('automation-status-info', status.services.automation_engine);

        // Get screen size and mouse position
        updateSystemInfo();

        addLog('✓ System status loaded');
    } catch (error) {
        addLog(`✗ Error loading status: ${error.message}`);
    }
}

// Update Engine Status
function updateEngineStatus(elementId, status) {
    const element = document.getElementById(elementId);
    if (element) {
        if (status === 'ready' || status === 'online') {
            element.textContent = '● READY';
            element.className = 'info-value status-online';
        } else {
            element.textContent = '● OFFLINE';
            element.className = 'info-value status-offline';
        }
    }
}

// Update System Info
async function updateSystemInfo() {
    try {
        // Get screen size
        const screenResponse = await axios.post(`${API_URL}/automation/run`, {
            action: 'screensize',
            params: {}
        });

        if (screenResponse.data.success) {
            document.getElementById('screen-size').textContent =
                `${screenResponse.data.width}x${screenResponse.data.height}`;
        }

        // Get mouse position
        const mouseResponse = await axios.post(`${API_URL}/automation/run`, {
            action: 'mousepos',
            params: {}
        });

        if (mouseResponse.data.success) {
            document.getElementById('mouse-pos').textContent =
                `(${mouseResponse.data.x}, ${mouseResponse.data.y})`;
        }
    } catch (error) {
        console.error('Error updating system info:', error);
    }
}

// Update mouse position periodically
setInterval(async () => {
    try {
        const response = await axios.post(`${API_URL}/automation/run`, {
            action: 'mousepos',
            params: {}
        });

        if (response.data.success) {
            document.getElementById('mouse-pos').textContent =
                `(${response.data.x}, ${response.data.y})`;
        }
    } catch (error) {
        // Silently fail
    }
}, 2000);

// Send Message
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    addLog(`💬 User: ${message}`);
    updateAuraStatus('PROCESSING...');
    userInput.value = '';

    try {
        const response = await axios.post(`${API_URL}/chat`, {
            message: message
        });

        displayResponse(response.data.response);
        addTask('Chat', message);
        updateAuraStatus('READY');
    } catch (error) {
        addLog(`✗ Error: ${error.message}`);
        updateAuraStatus('ERROR');
    }
}

// Voice Control
document.getElementById('voice-btn').addEventListener('click', async () => {
    const btn = document.getElementById('voice-btn');

    if (!isVoiceActive) {
        isVoiceActive = true;
        btn.classList.add('active');
        updateAuraStatus('LISTENING...');
        addLog('🎤 Voice recording started');

        try {
            const response = await axios.post(`${API_URL}/voice/start`);
            addLog(`🎤 ${response.data.message || 'Voice processing complete'}`);
        } catch (error) {
            addLog(`✗ Voice error: ${error.message}`);
        }

        isVoiceActive = false;
        btn.classList.remove('active');
        updateAuraStatus('READY');
    }
});

// Vision Mode
document.getElementById('vision-btn').addEventListener('click', async () => {
    updateAuraStatus('ANALYZING...');
    addLog('👁️ Vision analysis started');

    try {
        const response = await axios.post(`${API_URL}/vision/analyze`);

        if (response.data.status === 'success') {
            displayResponse(response.data.analysis);
            addTask('Vision', 'Screen analyzed');
        } else {
            addLog(`✗ Vision error: ${response.data.message}`);
        }

        updateAuraStatus('READY');
    } catch (error) {
        addLog(`✗ Vision error: ${error.message}`);
        updateAuraStatus('ERROR');
    }
});

// Automation Mode
document.getElementById('automation-btn').addEventListener('click', () => {
    showAutomationPanel();
});

// Wake Word Mode
document.getElementById('wakeword-btn').addEventListener('click', async () => {
    const btn = document.getElementById('wakeword-btn');

    if (!isWakeWordActive) {
        isWakeWordActive = true;
        btn.classList.add('active');
        updateAuraStatus('WAKE WORD ACTIVE');
        addLog('🔊 Wake word detection started');

        try {
            await axios.post(`${API_URL}/wakeword/start`);
        } catch (error) {
            addLog(`✗ Wake word error: ${error.message}`);
        }
    } else {
        isWakeWordActive = false;
        btn.classList.remove('active');
        updateAuraStatus('READY');
        addLog('🔊 Wake word detection stopped');

        try {
            await axios.post(`${API_URL}/wakeword/stop`);
        } catch (error) {
            addLog(`✗ Wake word error: ${error.message}`);
        }
    }
});

// Automation Panel
function showAutomationPanel() {
    const commands = [
        { name: 'Minimize All', action: 'minimize', params: {} },
        { name: 'Screenshot', action: 'screenshot', params: {} },
        { name: 'OCR Screen', action: 'ocr', params: {} }
    ];

    let html = '<div style="padding: 10px;">';
    html += '<h3 style="margin-bottom: 10px;">Quick Actions:</h3>';

    commands.forEach(cmd => {
        html += `<button onclick="executeQuickAction('${cmd.action}')" 
             style="display: block; width: 100%; margin: 5px 0; padding: 10px; 
             background: rgba(0,255,0,0.1); border: 1px solid #00ff00; 
             color: #00ff00; cursor: pointer; border-radius: 5px;">
             ${cmd.name}</button>`;
    });

    html += '</div>';
    displayResponse(html);
}

// Execute Quick Action
window.executeQuickAction = async function (action) {
    addLog(`⚙️ Executing: ${action}`);

    try {
        if (action === 'minimize') {
            await axios.post(`${API_URL}/automation/run`, {
                action: 'minimize',
                params: {}
            });
            addLog('✓ All windows minimized');
        } else if (action === 'screenshot') {
            await axios.post(`${API_URL}/vision/screenshot`);
            addLog('✓ Screenshot saved');
        } else if (action === 'ocr') {
            const response = await axios.post(`${API_URL}/vision/ocr`);
            if (response.data.status === 'success') {
                displayResponse(`OCR Text:\n${response.data.text}`);
            }
        }

        addTask('Automation', action);
    } catch (error) {
        addLog(`✗ Error: ${error.message}`);
    }
};

// Add Log Entry
function addLog(message) {
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    const timestamp = new Date().toLocaleTimeString();
    logEntry.textContent = `[${timestamp}] ${message}`;

    systemLogs.appendChild(logEntry);
    systemLogs.scrollTop = systemLogs.scrollHeight;

    // Keep only last 100 logs
    while (systemLogs.children.length > 100) {
        systemLogs.removeChild(systemLogs.firstChild);
    }
}

// Add Task to History
function addTask(type, description) {
    const taskItem = document.createElement('div');
    taskItem.className = 'task-item';
    const timestamp = new Date().toLocaleTimeString();

    taskItem.innerHTML = `
    <div style="font-weight: bold;">${type}</div>
    <div style="font-size: 11px; margin-top: 3px;">${description}</div>
    <div class="task-time">${timestamp}</div>
  `;

    taskHistory.insertBefore(taskItem, taskHistory.firstChild);

    // Keep only last 20 tasks
    while (taskHistory.children.length > 20) {
        taskHistory.removeChild(taskHistory.lastChild);
    }
}

// Display Response
function displayResponse(text) {
    responseDisplay.innerHTML = text.replace(/\n/g, '<br>');
    responseDisplay.classList.add('fade-in');
}

// Update AURA Status
function updateAuraStatus(status) {
    auraStatus.textContent = status;
}

// Send Button
document.getElementById('send-btn').addEventListener('click', sendMessage);

// Enter Key
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Initialize
setTimeout(() => {
    initSocket();
    addLog('⚡ MATLOOB AURA AI System Initialized');
    updateAuraStatus('INITIALIZING...');

    setTimeout(() => {
        updateAuraStatus('READY');
    }, 2000);
}, 500);


// ============================================
// SCROLL TO TOP FUNCTIONALITY
// ============================================

const scrollToTopBtn = document.getElementById('scrollToTop');
// Using existing variables: systemLogs, taskHistory, responseDisplay

// Show/Hide Scroll to Top button based on scroll position
function checkScrollPosition() {
    const logsScroll = systemLogs.scrollTop;
    const tasksScroll = taskHistory.scrollTop;

    if (logsScroll > 200 || tasksScroll > 200) {
        scrollToTopBtn.classList.add('show');
    } else {
        scrollToTopBtn.classList.remove('show');
    }
}

// Scroll to top with smooth animation
if (scrollToTopBtn) {
    scrollToTopBtn.addEventListener('click', () => {
        systemLogs.scrollTo({
            top: 0,
            behavior: 'smooth'
        });

        taskHistory.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Listen to scroll events
systemLogs.addEventListener('scroll', checkScrollPosition);
taskHistory.addEventListener('scroll', checkScrollPosition);

// Update scroll progress indicator
function updateScrollProgress() {
    const scrollPercentage = (systemLogs.scrollTop / (systemLogs.scrollHeight - systemLogs.clientHeight)) * 100;
    systemLogs.style.setProperty('--scroll-progress', `${scrollPercentage}%`);
}

systemLogs.addEventListener('scroll', updateScrollProgress);

// ============================================
// SMOOTH SCROLL FOR LOGS
// ============================================

// Auto-scroll handled in addLog function already

// ============================================
// PANEL ACTION BUTTONS
// ============================================

// Clear logs button
const clearLogsBtn = document.querySelector('.left-panel .panel-action');
if (clearLogsBtn) {
    clearLogsBtn.addEventListener('click', () => {
        if (confirm('Clear all system logs?')) {
            systemLogs.innerHTML = '';
            addLog('✓ System logs cleared');
        }
    });
}

// Clear task history button
const clearHistoryBtns = document.querySelectorAll('.right-panel .panel-action');
if (clearHistoryBtns.length > 1) {
    clearHistoryBtns[1].addEventListener('click', () => {
        if (confirm('Clear task history?')) {
            taskHistory.innerHTML = '';
            addLog('✓ Task history cleared');
        }
    });
}

// ============================================
// SCROLL ANIMATIONS
// ============================================

// Add fade-in animation to new log entries
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate__animated', 'animate__fadeInUp');
        }
    });
}, observerOptions);

// Observe log entries
const observeLogs = () => {
    document.querySelectorAll('.log-entry').forEach(log => {
        observer.observe(log);
    });
};

// Observe task items
const observeTasks = () => {
    document.querySelectorAll('.task-item').forEach(task => {
        observer.observe(task);
    });
};

// Call observers periodically
setInterval(() => {
    observeLogs();
    observeTasks();
}, 1000);

// ============================================
// CUSTOM SCROLLBAR INTERACTIONS
// ============================================

// Add hover effect to scrollable containers
[systemLogs, taskHistory, responseDisplay].forEach(container => {
    if (container) {
        container.addEventListener('mouseenter', () => {
            container.style.setProperty('--scrollbar-opacity', '1');
        });

        container.addEventListener('mouseleave', () => {
            container.style.setProperty('--scrollbar-opacity', '0.5');
        });
    }
});

// ============================================
// SCROLL SNAP FOR TASK HISTORY
// ============================================

let isScrolling;
taskHistory.addEventListener('scroll', () => {
    // Clear timeout
    window.clearTimeout(isScrolling);

    // Set timeout to run after scrolling ends
    isScrolling = setTimeout(() => {
        // Snap to nearest task item
        const taskItems = taskHistory.querySelectorAll('.task-item');
        let closestItem = null;
        let closestDistance = Infinity;

        taskItems.forEach(item => {
            const rect = item.getBoundingClientRect();
            const distance = Math.abs(rect.top - taskHistory.getBoundingClientRect().top);

            if (distance < closestDistance) {
                closestDistance = distance;
                closestItem = item;
            }
        });

        if (closestItem && closestDistance > 10) {
            closestItem.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }, 150);
});

console.log('✓ Scroll functionality initialized');
