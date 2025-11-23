// CommSync Web Receiver - Client-side JavaScript

// Socket.IO connection
const socket = io();

// State
let isReceiving = false;
let autoProcessEnabled = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    setupSocketHandlers();
    setupInputHandlers();
    addLog('System ready. Click "Start Receiving" to begin.', 'info');
});

// Socket.IO event handlers
function setupSocketHandlers() {
    socket.on('connect', function() {
        addLog('Connected to server', 'success');
    });

    socket.on('disconnect', function() {
        addLog('Disconnected from server', 'error');
    });

    socket.on('status', function(data) {
        updateStatus(data);
    });

    socket.on('update', function(data) {
        handleUpdate(data);
    });

    socket.on('stats', function(data) {
        updateStatus(data);
    });

    socket.on('session_reset', function() {
        addLog('Session reset', 'info');
        resetUI();
    });
}

// Input handling
function setupInputHandlers() {
    const inputArea = document.getElementById('input-area');

    // Real-time line processing when in receiving mode
    let buffer = '';
    inputArea.addEventListener('input', function(e) {
        if (!isReceiving) return;

        const value = inputArea.value;
        const lines = value.split('\n');

        // Process complete lines
        for (let i = 0; i < lines.length - 1; i++) {
            const line = lines[i];
            if (line.trim()) {
                socket.emit('input_line', { line: line });
            }
        }

        // Keep only the last incomplete line
        if (lines.length > 1) {
            inputArea.value = lines[lines.length - 1];
        }
    });

    // Handle paste events
    inputArea.addEventListener('paste', function(e) {
        if (!isReceiving) return;

        // Give a moment for the paste to complete
        setTimeout(() => {
            const text = inputArea.value;
            if (text.trim()) {
                socket.emit('paste_data', { text: text });
                inputArea.value = '';
            }
        }, 10);
    });
}

// Button handlers
function startReceiving() {
    isReceiving = true;
    const inputArea = document.getElementById('input-area');
    inputArea.classList.add('receiving');
    inputArea.value = '';
    inputArea.focus();

    document.getElementById('start-btn').disabled = true;
    document.getElementById('process-btn').disabled = false;

    addLog('Receiving mode activated. Waiting for transfer data...', 'info');
    updateSessionStatus('receiving');
}

function resetSession() {
    fetch('/api/reset', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            addLog(data.message, 'info');
            resetUI();
        })
        .catch(error => {
            addLog('Error resetting session: ' + error, 'error');
        });
}

function processInput() {
    const inputArea = document.getElementById('input-area');
    const text = inputArea.value;

    if (!text.trim()) {
        addLog('No input to process', 'error');
        return;
    }

    socket.emit('paste_data', { text: text });
    inputArea.value = '';
    addLog('Processing pasted input...', 'info');
}

function downloadData() {
    window.location.href = '/api/download';
    addLog('Downloading received data...', 'info');
}

// Update handlers
function handleUpdate(data) {
    const type = data.type;
    const message = data.message;

    switch (type) {
        case 'session_start':
            addLog(message, 'success');
            updateSessionStatus('receiving');
            document.getElementById('expected-size').textContent = formatBytes(data.expected_size);
            break;

        case 'frame':
            // Only log every 10th frame to avoid spam
            if (data.frame_count % 10 === 0) {
                addLog(`Frame ${data.frame_count}: ${formatBytes(data.bytes_received)} received`, 'frame');
            }
            updateProgress(data.progress_percent);
            break;

        case 'complete':
            addLog(message, 'success');
            updateSessionStatus('complete');
            showResults(data);
            break;

        case 'error':
            addLog('ERROR: ' + message, 'error');
            updateSessionStatus('error');
            showError(data);
            break;

        case 'info':
            addLog(message, 'info');
            break;
    }
}

function updateStatus(stats) {
    document.getElementById('frame-count').textContent = stats.frame_count || 0;
    document.getElementById('bytes-received').textContent = formatBytes(stats.bytes_received || 0);

    if (stats.expected_size) {
        document.getElementById('expected-size').textContent = formatBytes(stats.expected_size);
    }

    if (stats.progress_percent !== undefined) {
        updateProgress(stats.progress_percent);
    }

    updateSessionStatus(stats.status);
}

function updateSessionStatus(status) {
    const statusEl = document.getElementById('session-status');
    statusEl.className = 'status-value status-' + status;
    statusEl.textContent = status.charAt(0).toUpperCase() + status.slice(1);
}

function updateProgress(percent) {
    const fill = document.getElementById('progress-fill');
    const text = document.getElementById('progress-percent');

    fill.style.width = percent + '%';
    text.textContent = percent.toFixed(1) + '%';
}

function showResults(data) {
    // Hide error panel
    document.getElementById('error-panel').style.display = 'none';

    // Show results panel
    const resultsPanel = document.getElementById('results-panel');
    resultsPanel.style.display = 'block';

    // Update results
    document.getElementById('result-bytes').textContent = formatBytes(data.bytes_received);
    document.getElementById('result-frames').textContent = data.frame_count;
    document.getElementById('result-duration').textContent = data.duration_seconds.toFixed(2) + ' seconds';
    document.getElementById('result-speed').textContent = formatBytes(data.bytes_per_second) + '/s';

    // Show data preview
    document.getElementById('data-preview').textContent = data.data_preview || '<No preview available>';

    // Stop receiving mode
    isReceiving = false;
    const inputArea = document.getElementById('input-area');
    inputArea.classList.remove('receiving');
}

function showError(data) {
    // Hide results panel
    document.getElementById('results-panel').style.display = 'none';

    // Show error panel
    const errorPanel = document.getElementById('error-panel');
    errorPanel.style.display = 'block';

    let errorText = data.message;
    if (data.expected_hash && data.actual_hash) {
        errorText += '\n\nExpected hash: ' + data.expected_hash;
        errorText += '\nActual hash: ' + data.actual_hash;
    }

    document.getElementById('error-message').textContent = errorText;

    // Stop receiving mode
    isReceiving = false;
    const inputArea = document.getElementById('input-area');
    inputArea.classList.remove('receiving');
}

function resetUI() {
    isReceiving = false;

    // Reset status
    document.getElementById('session-status').className = 'status-value status-idle';
    document.getElementById('session-status').textContent = 'Idle';
    document.getElementById('frame-count').textContent = '0';
    document.getElementById('bytes-received').textContent = '0';
    document.getElementById('expected-size').textContent = '-';

    // Reset progress
    updateProgress(0);

    // Reset buttons
    document.getElementById('start-btn').disabled = false;
    document.getElementById('process-btn').disabled = true;

    // Reset input
    const inputArea = document.getElementById('input-area');
    inputArea.classList.remove('receiving');
    inputArea.value = '';

    // Hide result/error panels
    document.getElementById('results-panel').style.display = 'none';
    document.getElementById('error-panel').style.display = 'none';

    // Clear log (optional - comment out if you want to keep history)
    // document.getElementById('activity-log').innerHTML = '';
    // addLog('Ready for new transfer', 'info');
}

// Activity log
function addLog(message, type = 'info') {
    const logContainer = document.getElementById('activity-log');
    const entry = document.createElement('div');
    entry.className = 'log-entry log-' + type;

    const timestamp = new Date().toLocaleTimeString();
    entry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span>${escapeHtml(message)}`;

    logContainer.appendChild(entry);
    logContainer.scrollTop = logContainer.scrollHeight;

    // Limit log entries to prevent memory issues
    const maxEntries = 100;
    while (logContainer.children.length > maxEntries) {
        logContainer.removeChild(logContainer.firstChild);
    }
}

// Utility functions
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    if (!bytes) return '-';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + R to reset (prevent default browser refresh)
    if ((e.ctrlKey || e.metaKey) && e.key === 'r' && !isReceiving) {
        e.preventDefault();
        resetSession();
    }

    // Ctrl/Cmd + S to start receiving
    if ((e.ctrlKey || e.metaKey) && e.key === 's' && !isReceiving) {
        e.preventDefault();
        startReceiving();
    }
});
