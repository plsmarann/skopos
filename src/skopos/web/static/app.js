// skopos Web Dashboard JavaScript

let refreshInterval = 5000; // 5 seconds
let refreshTimer = null;
let countdownTimer = null;
let currentData = null;
let pendingKill = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('🛡️ skopos dashboard initialized');
    loadData();
    startAutoRefresh();
    setupFilters();
});

// Load detection data
async function loadData() {
    updateStatus('loading', 'Loading...');

    try {
        const [scanResp, statsResp] = await Promise.all([
            fetch('/api/scan'),
            fetch('/api/stats')
        ]);

        if (!scanResp.ok || !statsResp.ok) {
            throw new Error('API request failed');
        }

        const scanData = await scanResp.json();
        const statsData = await statsResp.json();

        if (!scanData.success || !statsData.success) {
            throw new Error(scanData.error || statsData.error || 'Unknown error');
        }

        currentData = scanData.findings;
        updateStats(statsData.stats);
        updateAgents(statsData.agents);
        updateTable(scanData.findings);
        updateStatus('connected', `Last updated: ${new Date().toLocaleTimeString()}`);

    } catch (error) {
        console.error('Error loading data:', error);
        updateStatus('error', `Error: ${error.message}`);
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
                    <button class="btn btn-danger" onclick="showKillModal(${proc.pid}, '${escapeHtml(proc.user)}', '${escapeHtml(proc.command)}')">Kill</button>
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
            updateStatus('connected', `✓ Killed process ${pid}`);
            // Refresh immediately
            setTimeout(loadData, 500);
        } else {
            alert(`Failed to kill process: ${data.error}`);
            updateStatus('error', `Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
        updateStatus('error', `Error: ${error.message}`);
    }
}

// Show process info (could expand to detailed modal)
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

// Auto-refresh functionality
function startAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer);
    if (countdownTimer) clearInterval(countdownTimer);

    refreshTimer = setInterval(loadData, refreshInterval);
    startCountdown();
}

function startCountdown() {
    let seconds = refreshInterval / 1000;
    const countdownEl = document.getElementById('refresh-countdown');

    if (countdownTimer) clearInterval(countdownTimer);

    countdownTimer = setInterval(() => {
        seconds--;
        if (seconds <= 0) {
            seconds = refreshInterval / 1000;
        }
        countdownEl.textContent = seconds;
    }, 1000);
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
