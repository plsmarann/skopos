// skopos Web Dashboard - Phase 2 (WebSocket Edition)

let socket = null;
let currentData = null;
let pendingKill = null;
let notificationsEnabled = false;

// Charts
let riskChart = null;
let timelineChart = null;
const timelineData = { labels: [], high: [], medium: [], low: [] };
const maxTimelinePoints = 10;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🛡️ skopos dashboard Phase 2 initialized');
    initializeCharts();
    connectWebSocket();
    setupFilters();
});

// WebSocket Connection
function connectWebSocket() {
    updateStatus('connecting', 'Connecting to WebSocket...');

    socket = io({
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 10
    });

    socket.on('connect', () => {
        console.log('✅ WebSocket connected');
        updateStatus('connected', 'Connected • Live updates active');
        document.getElementById('connection-type').textContent = 'WebSocket Connected';
    });

    socket.on('disconnect', () => {
        console.log('⚠️ WebSocket disconnected');
        updateStatus('error', 'Disconnected • Reconnecting...');
        document.getElementById('connection-type').textContent = 'Reconnecting...';
    });

    socket.on('status', (data) => {
        console.log('Status:', data.message);
    });

    socket.on('update', (data) => {
        handleUpdate(data);
    });

    socket.on('alert', (data) => {
        handleAlert(data);
    });

    socket.on('error', (data) => {
        console.error('Server error:', data.message);
        showToast(`Server error: ${data.message}`, 'error');
    });
}

// Handle real-time updates
function handleUpdate(data) {
    currentData = data.findings;
    updateStats(data.stats);
    updateAgents(data.agents);
    updateTable(data.findings);
    updateCharts(data.stats);
    updateTimeline(data.stats);

    // Show toast for changes
    if (data.changes.new.length > 0) {
        showToast(`${data.changes.new.length} new process(es) detected`, 'info');
    }
    if (data.changes.removed.length > 0) {
        showToast(`${data.changes.removed.length} process(es) stopped`, 'info');
    }

    updateStatus('connected', `Last update: ${new Date().toLocaleTimeString()}`);
}

// Handle high-severity alerts
function handleAlert(data) {
    console.warn('⚠️ High severity alert:', data);

    showToast(
        `🚨 HIGH RISK: PID ${data.pid} (${data.user})\n${data.command.substring(0, 50)}...`,
        'error',
        10000
    );

    // Browser notification
    if (notificationsEnabled && Notification.permission === 'granted') {
        new Notification('🛡️ skopos Alert', {
            body: `High-risk process detected:\nPID ${data.pid}: ${data.command.substring(0, 80)}`,
            icon: '/static/icon.png',
            requireInteraction: true
        });
    }

    // Play alert sound
    playAlertSound();
}

// Initialize Chart.js charts
function initializeCharts() {
    const ctx1 = document.getElementById('riskChart').getContext('2d');
    riskChart = new Chart(ctx1, {
        type: 'doughnut',
        data: {
            labels: ['High Risk', 'Medium Risk', 'Low Risk'],
            datasets: [{
                data: [0, 0, 0],
                backgroundColor: ['#f85149', '#d29922', '#3fb950'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#e6edf3' }
                }
            }
        }
    });

    const ctx2 = document.getElementById('timelineChart').getContext('2d');
    timelineChart = new Chart(ctx2, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'High',
                    data: [],
                    borderColor: '#f85149',
                    backgroundColor: 'rgba(248, 81, 73, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Medium',
                    data: [],
                    borderColor: '#d29922',
                    backgroundColor: 'rgba(210, 153, 34, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Low',
                    data: [],
                    borderColor: '#3fb950',
                    backgroundColor: 'rgba(63, 185, 80, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#7d8590' },
                    grid: { color: '#373e47' }
                },
                x: {
                    ticks: { color: '#7d8590' },
                    grid: { color: '#373e47' }
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#e6edf3' }
                }
            }
        }
    });
}

// Update charts with new data
function updateCharts(stats) {
    if (riskChart) {
        riskChart.data.datasets[0].data = [stats.high, stats.medium, stats.low];
        riskChart.update('none'); // No animation for performance
    }
}

// Update timeline chart
function updateTimeline(stats) {
    const now = new Date().toLocaleTimeString();

    timelineData.labels.push(now);
    timelineData.high.push(stats.high);
    timelineData.medium.push(stats.medium);
    timelineData.low.push(stats.low);

    // Keep only last N points
    if (timelineData.labels.length > maxTimelinePoints) {
        timelineData.labels.shift();
        timelineData.high.shift();
        timelineData.medium.shift();
        timelineData.low.shift();
    }

    if (timelineChart) {
        timelineChart.data.labels = timelineData.labels;
        timelineChart.data.datasets[0].data = timelineData.high;
        timelineChart.data.datasets[1].data = timelineData.medium;
        timelineChart.data.datasets[2].data = timelineData.low;
        timelineChart.update('none');
    }
}

// Update statistics cards
function updateStats(stats) {
    document.getElementById('stat-high').textContent = stats.high;
    document.getElementById('stat-medium').textContent = stats.medium;
    document.getElementById('stat-low').textContent = stats.low;
    document.getElementById('stat-total').textContent = stats.total;
}

// Update agents list
function updateAgents(agents) {
    const container = document.getElementById('agents-list');

    if (Object.keys(agents).length === 0) {
        container.innerHTML = '<div class="loading">No agents detected</div>';
        return;
    }

    container.innerHTML = Object.entries(agents)
        .map(([name, count]) => `
            <div class="agent-badge">
                <div class="agent-name">${escapeHtml(name)}</div>
                <div class="agent-count">${count} process${count > 1 ? 'es' : ''}</div>
            </div>
        `).join('');
}

// Update process table
function updateTable(findings) {
    const tbody = document.getElementById('process-tbody');

    if (findings.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">✓ No AI agents detected</td></tr>';
        return;
    }

    tbody.innerHTML = findings.map(f => {
        const proc = f.process;
        const keywords = [...f.ai_agent_keywords, ...f.model_keywords].join(', ') || '-';
        const ports = f.permissions?.listening_ports?.join(', ') || '-';
        const riskClass = f.severity;

        return `
            <tr class="row-${f.severity}" data-severity="${f.severity}">
                <td><span class="severity-badge severity-${f.severity}">${f.severity.toUpperCase()}</span></td>
                <td><span class="risk-score risk-${riskClass}">${f.risk_score}</span></td>
                <td>${proc.pid}</td>
                <td>${escapeHtml(proc.user)}</td>
                <td class="keywords">${escapeHtml(keywords)}</td>
                <td class="ports">${escapeHtml(ports)}</td>
                <td class="command" title="${escapeHtml(proc.command)}">${escapeHtml(proc.command)}</td>
                <td>
                    <button class="btn btn-info" onclick="showProcessInfo(${proc.pid})">Info</button>
                    <button class="btn btn-danger" onclick="showKillModal(${proc.pid}, '${escapeHtml(proc.user)}', \`${escapeHtml(proc.command)}\`)">Kill</button>
                </td>
            </tr>
        `;
    }).join('');

    applyFilters();
}

// Show kill confirmation modal
function showKillModal(pid, user, command) {
    pendingKill = pid;
    document.getElementById('kill-pid').textContent = pid;
    document.getElementById('kill-user').textContent = user;
    document.getElementById('kill-command').textContent = command;
    document.getElementById('kill-modal').classList.add('active');
}

// Close modal
function closeModal() {
    document.getElementById('kill-modal').classList.remove('active');
    pendingKill = null;
}

// Confirm and execute kill
async function confirmKill() {
    if (!pendingKill) return;

    const pid = pendingKill;
    closeModal();

    updateStatus('loading', `Killing process ${pid}...`);

    try {
        const resp = await fetch(`/api/kill/${pid}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ confirm: true })
        });

        const data = await resp.json();

        if (data.success) {
            showToast(`✓ Killed process ${pid}`, 'success');
            updateStatus('connected', `Killed PID ${pid}`);
        } else {
            showToast(`Failed to kill process: ${data.error}`, 'error');
            updateStatus('error', `Error: ${data.error}`);
        }
    } catch (error) {
        showToast(`Error: ${error.message}`, 'error');
        updateStatus('error', `Error: ${error.message}`);
    }
}

// Show process info
function showProcessInfo(pid) {
    const finding = currentData?.find(f => f.process.pid === pid);
    if (!finding) return;

    const info = `
PID: ${finding.process.pid}
User: ${finding.process.user}
Command: ${finding.process.command}
Executable: ${finding.process.executable || 'unknown'}
Risk Score: ${finding.risk_score}
Severity: ${finding.severity}
Keywords: ${[...finding.ai_agent_keywords, ...finding.model_keywords].join(', ') || 'none'}
Reasons: ${finding.reasons.join(', ')}
    `.trim();

    alert(info);
}

// Export data as JSON
function exportJSON() {
    if (!currentData) return;

    const dataStr = JSON.stringify(currentData, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `skopos-scan-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

// Update status indicator
function updateStatus(state, text) {
    const indicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');

    indicator.className = `status-indicator ${state}`;
    statusText.textContent = text;
}

// Filter setup
function setupFilters() {
    ['high', 'medium', 'low'].forEach(severity => {
        document.getElementById(`filter-${severity}`).addEventListener('change', applyFilters);
    });
}

function applyFilters() {
    const filters = {
        high: document.getElementById('filter-high').checked,
        medium: document.getElementById('filter-medium').checked,
        low: document.getElementById('filter-low').checked
    };

    document.querySelectorAll('#process-tbody tr').forEach(row => {
        const severity = row.dataset.severity;
        if (severity && !filters[severity]) {
            row.classList.add('hidden');
        } else {
            row.classList.remove('hidden');
        }
    });
}

// Toast notifications
function showToast(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => container.removeChild(toast), 300);
    }, duration);
}

// Request notification permission
function requestNotificationPermission() {
    if (!('Notification' in window)) {
        showToast('Browser notifications not supported', 'error');
        return;
    }

    Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
            notificationsEnabled = true;
            showToast('✓ Browser notifications enabled', 'success');
        } else {
            showToast('Notification permission denied', 'error');
        }
    });
}

// Play alert sound
function playAlertSound() {
    try {
        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBCx+zPDTijcJE2q88+OfTBAMTqfj8LZjHAU4kdfyzHksBSR3yPDekUAKE160xes=');
        audio.volume = 0.3;
        audio.play();
    } catch (e) {
        console.warn('Could not play alert sound:', e);
    }
}

// Utility: Escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
});
