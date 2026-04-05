/**
 * AI Sales Playbook Assistant — Frontend Application
 * Handles API communication, UI rendering, and user interactions.
 */

// ═══════════════ CONFIGURATION ═══════════════
const API_BASE = window.location.origin + '/api';

// ═══════════════ STATE ═══════════════
const state = {
    isLoading: false,
    conversations: [],
    playbookStats: null,
};

// ═══════════════ DOM ELEMENTS ═══════════════
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const elements = {
    sidebar: $('#sidebar'),
    sidebarToggle: $('#sidebarToggle'),
    menuBtn: $('#menuBtn'),
    newChatBtn: $('#newChatBtn'),
    queryInput: $('#queryInput'),
    sendBtn: $('#sendBtn'),
    chatArea: $('#chatArea'),
    welcomeScreen: $('#welcomeScreen'),
    messagesContainer: $('#messagesContainer'),
    historyList: $('#historyList'),
    seedBtn: $('#seedBtn'),
    clearHistoryBtn: $('#clearHistoryBtn'),
    toastContainer: $('#toastContainer'),
    pbStatusBadge: $('#pbStatusBadge'),
    pbChunkCount: $('#pbChunkCount'),
    pbCategoryCount: $('#pbCategoryCount'),
};

// ═══════════════ INITIALIZATION ═══════════════
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    loadPlaybookStats();
    loadHistory();
});

function initEventListeners() {
    // Sidebar toggle
    elements.sidebarToggle.addEventListener('click', () => {
        elements.sidebar.classList.toggle('collapsed');
    });

    elements.menuBtn.addEventListener('click', () => {
        elements.sidebar.classList.remove('collapsed');
    });

    // New chat
    elements.newChatBtn.addEventListener('click', resetChat);

    // Send query
    elements.sendBtn.addEventListener('click', handleSend);

    // Textarea auto-resize & Enter key
    elements.queryInput.addEventListener('input', autoResize);
    elements.queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    // Example cards
    $$('.example-card').forEach((card) => {
        card.addEventListener('click', () => {
            const query = card.dataset.query;
            elements.queryInput.value = query;
            autoResize();
            handleSend();
        });
    });

    // Seed playbook
    elements.seedBtn.addEventListener('click', seedPlaybook);

    // Clear history
    elements.clearHistoryBtn.addEventListener('click', clearAllHistory);
}

// ═══════════════ API CALLS ═══════════════

async function apiCall(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const defaultHeaders = { 'Content-Type': 'application/json' };

    try {
        const response = await fetch(url, {
            headers: { ...defaultHeaders, ...options.headers },
            ...options,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            let detail = error.detail || `HTTP ${response.status}`;
            if (Array.isArray(detail)) {
                detail = detail.map(e => e.msg || JSON.stringify(e)).join(', ');
            } else if (typeof detail === 'object') {
                detail = JSON.stringify(detail);
            }
            throw new Error(detail);
        }

        return await response.json();
    } catch (err) {
        if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
            throw new Error('Cannot connect to server. Make sure both FastAPI and Flask servers are running.');
        }
        throw err;
    }
}

async function queryObjection(query) {
    return apiCall('/query', {
        method: 'POST',
        body: JSON.stringify({ query, top_k: 5 }),
    });
}

async function getPlaybookStats() {
    return apiCall('/playbook/stats');
}

async function seedPlaybookAPI(force = true) {
    return apiCall('/playbook/seed', {
        method: 'POST',
        body: JSON.stringify({ force }),
    });
}

async function getHistory() {
    return apiCall('/history');
}

async function deleteConversation(id) {
    return apiCall(`/history/${id}`, { method: 'DELETE' });
}

async function clearHistory() {
    return apiCall('/history', { method: 'DELETE' });
}

// ═══════════════ MAIN HANDLERS ═══════════════

async function handleSend() {
    const query = elements.queryInput.value.trim();
    if (!query || state.isLoading) return;

    state.isLoading = true;
    elements.sendBtn.disabled = true;

    // Hide welcome screen, show messages
    elements.welcomeScreen.classList.add('hidden');
    elements.messagesContainer.style.display = 'flex';

    // Add user message
    addUserMessage(query);

    // Clear input
    elements.queryInput.value = '';
    autoResize();

    // Add loading indicator
    const loadingId = addLoadingMessage();

    try {
        const result = await queryObjection(query);

        // Remove loading
        removeMessage(loadingId);

        // Add assistant message
        addAssistantMessage(result.response, result.retrieved_chunks);

        // Refresh history
        await loadHistory();

        // Scroll to bottom
        scrollToBottom();

    } catch (err) {
        removeMessage(loadingId);
        addErrorMessage(err.message);
        showToast(err.message, 'error');
    } finally {
        state.isLoading = false;
        elements.sendBtn.disabled = false;
        elements.queryInput.focus();
    }
}

async function seedPlaybook() {
    elements.seedBtn.disabled = true;
    elements.seedBtn.textContent = 'Seeding...';

    try {
        const result = await seedPlaybookAPI(true);
        showToast(result.message, 'success');
        await loadPlaybookStats();
    } catch (err) {
        showToast(`Seed failed: ${err.message}`, 'error');
    } finally {
        elements.seedBtn.disabled = false;
        elements.seedBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Seed Playbook
        `;
    }
}

async function loadPlaybookStats() {
    try {
        const stats = await getPlaybookStats();
        state.playbookStats = stats;

        elements.pbStatusBadge.textContent = stats.status;
        elements.pbStatusBadge.className = `status-badge ${stats.status}`;
        elements.pbChunkCount.textContent = stats.total_chunks;
        elements.pbCategoryCount.textContent = stats.categories.length;
    } catch (err) {
        elements.pbStatusBadge.textContent = 'Error';
        elements.pbStatusBadge.className = 'status-badge empty';
        console.error('Failed to load playbook stats:', err);
    }
}

async function loadHistory() {
    try {
        const data = await getHistory();
        state.conversations = data.conversations || [];
        renderHistoryList();
    } catch (err) {
        console.error('Failed to load history:', err);
    }
}

async function clearAllHistory() {
    if (!confirm('Delete all conversation history?')) return;
    try {
        await clearHistory();
        state.conversations = [];
        renderHistoryList();
        showToast('History cleared', 'success');
    } catch (err) {
        showToast(`Failed: ${err.message}`, 'error');
    }
}

function resetChat() {
    elements.welcomeScreen.classList.remove('hidden');
    elements.messagesContainer.style.display = 'none';
    elements.messagesContainer.innerHTML = '';
    elements.queryInput.value = '';
    elements.queryInput.focus();
}

// ═══════════════ MESSAGE RENDERING ═══════════════

let messageCounter = 0;

function addUserMessage(text) {
    const id = `msg-${++messageCounter}`;
    const html = `
        <div class="message message-user" id="${id}">
            <div class="message-bubble">${escapeHtml(text)}</div>
        </div>
    `;
    elements.messagesContainer.insertAdjacentHTML('beforeend', html);
    scrollToBottom();
    return id;
}

function addAssistantMessage(markdown, chunks = []) {
    const id = `msg-${++messageCounter}`;
    const renderedContent = renderMarkdown(markdown);

    let chunksHtml = '';
    if (chunks && chunks.length > 0) {
        const badges = chunks.map(c => `
            <span class="chunk-badge">
                ${escapeHtml(c.objection_type)}
                <span class="similarity">${(c.similarity * 100).toFixed(0)}%</span>
            </span>
        `).join('');
        chunksHtml = `<div class="retrieved-info">${badges}</div>`;
    }

    const html = `
        <div class="message message-assistant" id="${id}">
            <div class="message-assistant-header">
                <div class="assistant-avatar">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        <path d="M2 17l10 5 10-5"/>
                        <path d="M2 12l10 5 10-5"/>
                    </svg>
                </div>
                <span class="assistant-name">SalesAI</span>
            </div>
            <div class="message-content">
                ${renderedContent}
                ${chunksHtml}
            </div>
        </div>
    `;
    elements.messagesContainer.insertAdjacentHTML('beforeend', html);
    scrollToBottom();
    return id;
}

function addLoadingMessage() {
    const id = `msg-${++messageCounter}`;
    const html = `
        <div class="message message-assistant" id="${id}">
            <div class="message-assistant-header">
                <div class="assistant-avatar">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                        <path d="M2 17l10 5 10-5"/>
                        <path d="M2 12l10 5 10-5"/>
                    </svg>
                </div>
                <span class="assistant-name">SalesAI</span>
            </div>
            <div class="message-content message-loading">
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
                <span style="color: var(--text-tertiary); font-size: 0.8rem; margin-left: 4px;">
                    Searching playbook & generating suggestions...
                </span>
            </div>
        </div>
    `;
    elements.messagesContainer.insertAdjacentHTML('beforeend', html);
    scrollToBottom();
    return id;
}

function addErrorMessage(error) {
    const id = `msg-${++messageCounter}`;
    const html = `
        <div class="message message-assistant" id="${id}">
            <div class="message-content" style="border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.05);">
                <p style="color: var(--error);">⚠️ <strong>Error:</strong> ${escapeHtml(error)}</p>
                <p style="color: var(--text-tertiary); font-size: 0.8rem; margin-top: 8px;">
                    Make sure the backend server is running and your API keys are configured.
                </p>
            </div>
        </div>
    `;
    elements.messagesContainer.insertAdjacentHTML('beforeend', html);
    scrollToBottom();
    return id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// ═══════════════ HISTORY RENDERING ═══════════════

function renderHistoryList() {
    if (state.conversations.length === 0) {
        elements.historyList.innerHTML = '<div class="history-empty"><p>No conversations yet</p></div>';
        return;
    }

    const html = state.conversations.slice(0, 30).map(conv => {
        const time = formatTime(conv.created_at);
        const preview = conv.query.length > 40 ? conv.query.slice(0, 40) + '...' : conv.query;
        return `
            <div class="history-item" data-id="${conv.id}">
                <div class="history-icon">💬</div>
                <div class="history-text">
                    <div class="history-title">${escapeHtml(preview)}</div>
                    <div class="history-time">${time}</div>
                </div>
                <button class="history-delete" onclick="event.stopPropagation(); deleteHistoryItem(${conv.id})" title="Delete">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            </div>
        `;
    }).join('');

    elements.historyList.innerHTML = html;

    // Add click handlers to show conversation
    elements.historyList.querySelectorAll('.history-item').forEach(item => {
        item.addEventListener('click', () => {
            const id = parseInt(item.dataset.id);
            showConversation(id);
        });
    });
}

function showConversation(id) {
    const conv = state.conversations.find(c => c.id === id);
    if (!conv) return;

    elements.welcomeScreen.classList.add('hidden');
    elements.messagesContainer.style.display = 'flex';
    elements.messagesContainer.innerHTML = '';

    addUserMessage(conv.query);
    addAssistantMessage(conv.response, conv.retrieved_chunks);
}

async function deleteHistoryItem(id) {
    try {
        await deleteConversation(id);
        state.conversations = state.conversations.filter(c => c.id !== id);
        renderHistoryList();
        showToast('Conversation deleted', 'success');
    } catch (err) {
        showToast(`Delete failed: ${err.message}`, 'error');
    }
}

// ═══════════════ MARKDOWN RENDERER ═══════════════

function renderMarkdown(text) {
    if (!text) return '';

    let html = escapeHtml(text);

    // Horizontal rules
    html = html.replace(/^---$/gm, '<hr>');

    // Headers
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Blockquotes
    html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');

    // Merge consecutive blockquotes
    html = html.replace(/<\/blockquote>\n<blockquote>/g, '\n');

    // Unordered lists
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

    // Numbered lists
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

    // Inline code
    html = html.replace(/`(.+?)`/g, '<code>$1</code>');

    // Paragraphs — wrap remaining lines
    html = html.replace(/^(?!<[hublop]|<\/|<hr)(.+)$/gm, '<p>$1</p>');

    // Clean up extra newlines
    html = html.replace(/\n{2,}/g, '\n');

    return html;
}

// ═══════════════ UTILITY FUNCTIONS ═══════════════

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function autoResize() {
    const textarea = elements.queryInput;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        elements.chatArea.scrollTop = elements.chatArea.scrollHeight;
    });
}

function formatTime(dateStr) {
    try {
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`;

        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
        return '';
    }
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const icons = {
        success: '✓',
        error: '✕',
        info: 'ℹ',
    };

    toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span> ${escapeHtml(message)}`;
    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// Make deleteHistoryItem available globally for onclick handlers
window.deleteHistoryItem = deleteHistoryItem;
