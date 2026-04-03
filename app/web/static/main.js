/* ═══════════════════════════════════════════════════════════════════
   CLAIRE OBSERVABILITY — main.js
   WebSocket live feed · Agents grid · Modals · Toasts · Filtering
   ═══════════════════════════════════════════════════════════════════ */

'use strict';

// ── Config ─────────────────────────────────────────────────────────────────
const API_TOKEN = 'changeme'; // read from meta or env in production
const WS_URL    = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/api/v1/ws/live`;

const INTEG_COLORS = {
  n8n:    '#ea4b71',
  make:   '#7c3aed',
  claude: '#d97706',
  openai: '#10b981',
  gemini: '#3b82f6',
  custom: '#64748b',
};

const PIXEL_AVATARS = {
  n8n: `<svg width="48" height="48" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
    <rect x="3" y="1" width="4" height="1" fill="#ea4b71"/>
    <rect x="2" y="2" width="6" height="3" fill="#ea4b71"/>
    <rect x="3" y="2" width="1" height="1" fill="#060b18"/>
    <rect x="6" y="2" width="1" height="1" fill="#060b18"/>
    <rect x="3" y="4" width="4" height="1" fill="#c83056"/>
    <rect x="1" y="5" width="8" height="3" fill="#ea4b71"/>
    <rect x="2" y="8" width="2" height="2" fill="#ea4b71"/>
    <rect x="6" y="8" width="2" height="2" fill="#ea4b71"/>
    <rect x="0" y="6" width="1" height="1" fill="#c83056"/>
    <rect x="9" y="6" width="1" height="1" fill="#c83056"/>
  </svg>`,
  make: `<svg width="48" height="48" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
    <rect x="3" y="0" width="4" height="2" fill="#7c3aed"/>
    <rect x="2" y="2" width="6" height="1" fill="#a855f7"/>
    <rect x="1" y="3" width="8" height="3" fill="#7c3aed"/>
    <rect x="2" y="3" width="1" height="1" fill="#060b18"/>
    <rect x="7" y="3" width="1" height="1" fill="#060b18"/>
    <rect x="3" y="5" width="4" height="1" fill="#5b21b6"/>
    <rect x="2" y="6" width="6" height="2" fill="#7c3aed"/>
    <rect x="3" y="8" width="1" height="2" fill="#7c3aed"/>
    <rect x="6" y="8" width="1" height="2" fill="#7c3aed"/>
  </svg>`,
  claude: `<svg width="48" height="48" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
    <rect x="2" y="1" width="6" height="1" fill="#d97706"/>
    <rect x="1" y="2" width="8" height="4" fill="#d97706"/>
    <rect x="2" y="3" width="1" height="1" fill="#fff7ed"/>
    <rect x="7" y="3" width="1" height="1" fill="#fff7ed"/>
    <rect x="3" y="5" width="4" height="1" fill="#92400e"/>
    <rect x="2" y="6" width="6" height="2" fill="#d97706"/>
    <rect x="0" y="3" width="1" height="2" fill="#b45309"/>
    <rect x="9" y="3" width="1" height="2" fill="#b45309"/>
    <rect x="3" y="8" width="4" height="2" fill="#d97706"/>
  </svg>`,
  openai: `<svg width="48" height="48" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
    <rect x="3" y="0" width="4" height="2" fill="#10b981"/>
    <rect x="2" y="2" width="6" height="4" fill="#10b981"/>
    <rect x="3" y="3" width="1" height="1" fill="#064e3b"/>
    <rect x="6" y="3" width="1" height="1" fill="#064e3b"/>
    <rect x="3" y="5" width="4" height="1" fill="#059669"/>
    <rect x="1" y="6" width="8" height="2" fill="#10b981"/>
    <rect x="2" y="8" width="2" height="2" fill="#10b981"/>
    <rect x="6" y="8" width="2" height="2" fill="#10b981"/>
  </svg>`,
  gemini: `<svg width="48" height="48" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
    <rect x="4" y="0" width="2" height="1" fill="#3b82f6"/>
    <rect x="3" y="1" width="4" height="1" fill="#3b82f6"/>
    <rect x="2" y="2" width="6" height="3" fill="#3b82f6"/>
    <rect x="3" y="3" width="1" height="1" fill="#eff6ff"/>
    <rect x="6" y="3" width="1" height="1" fill="#eff6ff"/>
    <rect x="2" y="5" width="6" height="1" fill="#1d4ed8"/>
    <rect x="3" y="6" width="4" height="2" fill="#3b82f6"/>
    <rect x="2" y="8" width="1" height="2" fill="#3b82f6"/>
    <rect x="7" y="8" width="1" height="2" fill="#3b82f6"/>
    <rect x="4" y="8" width="2" height="1" fill="#60a5fa"/>
  </svg>`,
  custom: `<svg width="48" height="48" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
    <rect x="3" y="1" width="4" height="2" fill="#64748b"/>
    <rect x="2" y="3" width="6" height="3" fill="#64748b"/>
    <rect x="3" y="4" width="1" height="1" fill="#0f172a"/>
    <rect x="6" y="4" width="1" height="1" fill="#0f172a"/>
    <rect x="3" y="6" width="4" height="1" fill="#475569"/>
    <rect x="2" y="7" width="6" height="2" fill="#64748b"/>
    <rect x="3" y="9" width="2" height="1" fill="#64748b"/>
    <rect x="5" y="9" width="2" height="1" fill="#64748b"/>
  </svg>`,
};

// ── State ───────────────────────────────────────────────────────────────────
let ws = null;
let wsReconnectTimer = null;
let agents = {};          // { agent_id: Agent }
let currentFilter = 'all';
let logCount = 0;
const MAX_LOGS = 200;

// ── WebSocket ───────────────────────────────────────────────────────────────

function connectWS() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;

  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    setWsStatus('Connecté', true);
    clearTimeout(wsReconnectTimer);
  };

  ws.onmessage = (evt) => {
    let msg;
    try { msg = JSON.parse(evt.data); } catch { return; }

    switch (msg.type) {
      case 'init':
        (msg.agents || []).forEach(a => { agents[a.agent_id] = a; });
        renderAgentsGrid();
        updateKPIs();
        break;
      case 'logs_history':
        (msg.logs || []).forEach(appendLog);
        break;
      case 'log':
        appendLog(msg.data);
        break;
      case 'agent_update':
        agents[msg.data.agent_id] = msg.data;
        updateAgentCard(msg.data);
        updateKPIs();
        break;
      case 'agent_deleted':
        delete agents[msg.data.agent_id];
        removeAgentCard(msg.data.agent_id);
        updateKPIs();
        break;
    }
  };

  ws.onclose = () => {
    setWsStatus('Reconnexion...', false);
    wsReconnectTimer = setTimeout(connectWS, 3000);
  };

  ws.onerror = () => {
    setWsStatus('Erreur WS', false);
  };
}

function setWsStatus(text, ok) {
  const el = document.getElementById('ws-status');
  if (el) el.textContent = text;
  const pill = el && el.closest('.status-pill');
  if (pill) {
    pill.style.borderColor = ok ? 'rgba(74,222,128,0.3)' : 'rgba(251,191,36,0.3)';
    pill.style.color       = ok ? 'var(--green)' : 'var(--paused)';
  }
  // update sidebar running count
  updateSidebarBadge();
}

// ── Agent Card Rendering ────────────────────────────────────────────────────

function buildAgentCard(agent) {
  const color   = INTEG_COLORS[agent.integration] || '#64748b';
  const avatar  = PIXEL_AVATARS[agent.integration] || PIXEL_AVATARS.custom;
  const status  = agent.status || 'idle';
  const task    = agent.current_task || '';
  const sr      = agent.success_rate ?? 100;

  const isRunning = status === 'running';
  const isPaused  = status === 'paused';

  return `
  <div class="agent-card" data-agent-id="${agent.agent_id}" data-status="${status}">
    <div class="agent-card-top">
      <div class="pixel-avatar avatar-${agent.integration}" style="position:relative">
        ${avatar}
        <div class="pixel-status-ring" style="--status-color: var(--${status})"></div>
      </div>
      <div class="agent-info">
        <div class="agent-name">${escHtml(agent.name)}</div>
        <div class="agent-integration">
          <span class="integration-dot" style="background:${color}"></span>
          ${agent.integration.toUpperCase()}
        </div>
      </div>
      <div class="status-badge status-${status}">
        <span class="led"></span>
        ${status.toUpperCase()}
      </div>
    </div>

    <div class="agent-stats">
      <div class="agent-stat">
        <div class="stat-val">${agent.runs_today ?? 0}</div>
        <div class="stat-lbl">Runs</div>
      </div>
      <div class="agent-stat">
        <div class="stat-val">${agent.errors_today ?? 0}</div>
        <div class="stat-lbl">Erreurs</div>
      </div>
      <div class="agent-stat">
        <div class="stat-val">${sr}%</div>
        <div class="stat-lbl">Succès</div>
      </div>
    </div>

    <div class="agent-task">
      ${task
        ? `<span class="task-cursor"></span><span>${escHtml(task)}</span>`
        : `<span style="opacity:.4">— en attente —</span>`}
    </div>

    <div class="agent-actions">
      ${isRunning || isPaused
        ? `<button class="btn-icon" onclick="togglePause('${agent.agent_id}', '${status}')">
             ${isRunning
               ? `<svg width="12" height="12" fill="currentColor" viewBox="0 0 24 24"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg> Pause`
               : `<svg width="12" height="12" fill="currentColor" viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21"/></svg> Run`}
           </button>`
        : `<button class="btn-icon" onclick="resumeAgent('${agent.agent_id}')">
             <svg width="12" height="12" fill="currentColor" viewBox="0 0 24 24"><polygon points="5,3 19,12 5,21"/></svg> Run
           </button>`}
      <button class="btn-icon" onclick="showAgentLogs('${agent.agent_id}', '${escHtml(agent.name)}')">
        <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14,2 14,8 20,8"/>
        </svg>
        Logs
      </button>
      <button class="btn-icon danger" onclick="deleteAgent('${agent.agent_id}', '${escHtml(agent.name)}')">
        <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <polyline points="3,6 5,6 21,6"/>
          <path d="M19,6l-1,14a2,2,0,0,1-2,2H8a2,2,0,0,1-2-2L5,6"/>
        </svg>
      </button>
    </div>
  </div>`;
}

function renderAgentsGrid() {
  const grid = document.getElementById('agents-grid');
  if (!grid) return;

  const list = Object.values(agents).filter(a =>
    currentFilter === 'all' || a.status === currentFilter
  );

  if (list.length === 0) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1">
        <div class="empty-icon">&#x1F916;</div>
        <div class="empty-title">Aucun agent${currentFilter !== 'all' ? ' dans ce filtre' : ''}</div>
        <div class="empty-sub">${currentFilter === 'all'
          ? 'Cliquez sur "Ajouter un agent" ou connectez une intégration.'
          : 'Essayez un autre filtre.'}</div>
      </div>`;
    return;
  }

  grid.innerHTML = list.map(buildAgentCard).join('');
}

function updateAgentCard(agent) {
  const existing = document.querySelector(`[data-agent-id="${agent.agent_id}"]`);
  agents[agent.agent_id] = agent;

  if (existing) {
    const fits = currentFilter === 'all' || agent.status === currentFilter;
    if (fits) {
      const tmp = document.createElement('div');
      tmp.innerHTML = buildAgentCard(agent);
      const newCard = tmp.firstElementChild;
      newCard.style.animation = 'log-in .3s ease';
      existing.replaceWith(newCard);
    } else {
      existing.remove();
    }
  } else {
    // New agent — prepend to grid
    if (currentFilter === 'all' || agent.status === currentFilter) {
      const grid = document.getElementById('agents-grid');
      if (grid) {
        const empty = grid.querySelector('.empty-state');
        if (empty) empty.remove();
        const tmp = document.createElement('div');
        tmp.innerHTML = buildAgentCard(agent);
        grid.prepend(tmp.firstElementChild);
      }
    }
  }
}

function removeAgentCard(agentId) {
  const card = document.querySelector(`[data-agent-id="${agentId}"]`);
  if (card) {
    card.style.opacity = '0';
    card.style.transform = 'scale(.95)';
    card.style.transition = 'all .2s';
    setTimeout(() => {
      card.remove();
      const grid = document.getElementById('agents-grid');
      if (grid && grid.children.length === 0) renderAgentsGrid();
    }, 200);
  }
}

// ── KPIs ────────────────────────────────────────────────────────────────────

function updateKPIs() {
  const list    = Object.values(agents);
  const total   = list.length;
  const running = list.filter(a => a.status === 'running').length;
  const error   = list.filter(a => a.status === 'error').length;
  const avgSr   = total ? Math.round(list.reduce((s, a) => s + (a.success_rate ?? 100), 0) / total) : 100;

  setText('kpi-total',   total);
  setText('kpi-running', running);
  setText('kpi-error',   error);
  setText('kpi-sr',      `${avgSr}%`);
  updateSidebarBadge(running);
}

function updateSidebarBadge(running) {
  const badge = document.getElementById('sidebar-running');
  if (badge) badge.textContent = running ?? Object.values(agents).filter(a => a.status === 'running').length;
}

// ── Live Log Console ────────────────────────────────────────────────────────

function appendLog(log) {
  const body = document.getElementById('log-body');
  if (!body) return;

  logCount++;
  if (logCount > MAX_LOGS) {
    const first = body.firstElementChild;
    if (first) first.remove();
  }

  const time = new Date(log.timestamp).toLocaleTimeString('fr-FR', {
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
  const level   = log.level || 'INFO';
  const source  = log.source || 'system';
  const message = escHtml(log.message || '');

  const line = document.createElement('div');
  line.className = 'log-line';
  line.innerHTML = `
    <span class="log-time">${time}</span>
    <span class="log-level level-${level}">${level}</span>
    <span class="log-msg"><span class="log-source">${escHtml(source)}</span> · ${message}</span>`;

  body.appendChild(line);
  body.scrollTop = body.scrollHeight;
}

function clearLogs() {
  const body = document.getElementById('log-body');
  if (body) { body.innerHTML = ''; logCount = 0; }
}

// ── Agent actions ───────────────────────────────────────────────────────────

async function apiPatch(path, body) {
  return fetch(path, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${API_TOKEN}` },
    body: JSON.stringify(body),
  });
}

async function apiDelete(path) {
  return fetch(path, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${API_TOKEN}` },
  });
}

async function apiPost(path, body) {
  return fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${API_TOKEN}` },
    body: JSON.stringify(body),
  });
}

async function togglePause(agentId, currentStatus) {
  const newStatus = currentStatus === 'running' ? 'paused' : 'running';
  const resp = await apiPatch(`/api/v1/agents/${agentId}/status`, { status: newStatus });
  if (!resp.ok) showToast('Erreur lors du changement de statut', 'error');
}

async function resumeAgent(agentId) {
  const resp = await apiPatch(`/api/v1/agents/${agentId}/status`, { status: 'running', current_task: 'Démarrage manuel...' });
  if (!resp.ok) showToast('Impossible de démarrer l\'agent', 'error');
}

async function deleteAgent(agentId, name) {
  if (!confirm(`Supprimer l'agent "${name}" ? Cette action est irréversible.`)) return;
  const resp = await apiDelete(`/api/v1/agents/${agentId}`);
  if (resp.ok) {
    showToast(`Agent "${name}" supprimé`, 'info');
  } else {
    showToast('Erreur lors de la suppression', 'error');
  }
}

function showAgentLogs(agentId, name) {
  const agentLogs = Object.values(agents[agentId] ? [agents[agentId]] : []);
  // Filter logs from the log bus (approximation — real impl would filter server-side)
  document.getElementById('modal-content').innerHTML = `
    <h2 class="modal-title">Logs — ${escHtml(name)}</h2>
    <div class="log-console" style="border:1px solid var(--border)">
      <div class="log-console-body" id="modal-log-body" style="height:260px">
        <div class="log-line">
          <span class="log-time">—</span>
          <span class="log-level level-INFO">INFO</span>
          <span class="log-msg">Affichage des logs en cours... consultez le flux live ci-dessous.</span>
        </div>
      </div>
    </div>
    <div class="modal-actions">
      <button class="btn btn-ghost" onclick="closeModal()">Fermer</button>
      <a class="btn btn-secondary" href="/dashboard">Dashboard complet</a>
    </div>`;
  openModal();
}

// ── Add Agent Modal ─────────────────────────────────────────────────────────

function openAddAgentModal() {
  document.getElementById('modal-content').innerHTML = `
    <h2 class="modal-title">Ajouter un agent</h2>
    <div style="display:flex;flex-direction:column;gap:1rem">
      <div class="form-group">
        <label class="form-label">Nom de l'agent</label>
        <input class="form-input" id="new-agent-name" type="text" placeholder="Mon agent n8n" autofocus>
      </div>
      <div class="form-group">
        <label class="form-label">Intégration</label>
        <select class="form-select" id="new-agent-integ">
          <option value="n8n">n8n</option>
          <option value="make">Make</option>
          <option value="claude">Claude (Anthropic)</option>
          <option value="openai">ChatGPT / OpenAI</option>
          <option value="gemini">Gemini (Google)</option>
          <option value="custom">Personnalisé</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Tags (séparés par des virgules)</label>
        <input class="form-input" id="new-agent-tags" type="text" placeholder="automation, production">
      </div>
    </div>
    <div class="modal-actions">
      <button class="btn btn-ghost" onclick="closeModal()">Annuler</button>
      <button class="btn btn-primary" onclick="confirmAddAgent()">Créer</button>
    </div>`;
  openModal();
}

async function confirmAddAgent() {
  const name   = document.getElementById('new-agent-name').value.trim();
  const integ  = document.getElementById('new-agent-integ').value;
  const tagsRaw = document.getElementById('new-agent-tags').value;
  const tags   = tagsRaw.split(',').map(t => t.trim()).filter(Boolean);

  if (!name) { showToast('Le nom est requis', 'error'); return; }

  const resp = await apiPost('/api/v1/agents', { name, integration: integ, tags });
  closeModal();
  if (resp.ok) {
    showToast(`Agent "${name}" créé`, 'success');
  } else {
    showToast('Erreur lors de la création', 'error');
  }
}

// ── Filtering ───────────────────────────────────────────────────────────────

function initFilters() {
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.filter;
      renderAgentsGrid();
    });
  });
}

// ── Modals ──────────────────────────────────────────────────────────────────

function openModal() {
  document.getElementById('modal-overlay').classList.add('open');
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});

// Close on overlay click
document.addEventListener('click', e => {
  if (e.target.id === 'modal-overlay') closeModal();
});

// ── Toast notifications ─────────────────────────────────────────────────────

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icons = { success: '✓', error: '✕', info: 'i' };
  toast.innerHTML = `<span style="font-weight:900">${icons[type] || 'i'}</span> ${escHtml(message)}`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3100);
}

// ── Utilities ───────────────────────────────────────────────────────────────

function escHtml(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

// ── Bootstrap ───────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Hydrate from server-side data if available (agents page)
  if (window.__AGENTS__) {
    window.__AGENTS__.forEach(a => { agents[a.agent_id] = a; });
    renderAgentsGrid();
    updateKPIs();
  }

  initFilters();
  connectWS();
});
