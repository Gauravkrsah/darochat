/**
 * Daro Chat — Frontend Logic
 * Streaming SSE, markdown rendering, light/dark theme, responsive sidebar
 * Includes Local Storage for multi-session recent chat history.
 */

// ── State ──────────────────────────────────────────────────────────────────
const state = {
    messages: [],
    streaming: false,
    abortCtrl: null,
    systemPrompt: 'You are a helpful, harmless, and honest AI assistant.',
    currentChatId: null,
    chats: [] // Array of { id, title, updatedAt, messages }
};

// ── DOM ────────────────────────────────────────────────────────────────────
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const messagesEl = $('#messages');
const welcomeEl = $('#welcome');
const inputEl = $('#input');
const btnSend = $('#btn-send');
const btnStop = $('#btn-stop');
const modelSelect = $('#model-select');
const topbarModel = $('#topbar-model');
const tempSlider = $('#temp-slider');
const tempVal = $('#temp-val');
const sidebar = $('#sidebar');
const overlay = $('#sidebar-overlay');
const btnNewChat = $('#btn-new-chat');
const recentList = $('#recent-list');

// ── Init ───────────────────────────────────────────────────────────────────
function init() {
    // Load saved theme
    const saved = localStorage.getItem('nim-theme') || 'dark';
    setTheme(saved);

    // Load recent chats from localStorage
    loadChats();

    // Start a new empty chat
    newChat();

    // Events
    inputEl.addEventListener('input', autoResize);
    inputEl.addEventListener('keydown', onKeydown);
    btnSend.addEventListener('click', send);
    btnStop.addEventListener('click', stop);
    btnNewChat.addEventListener('click', newChat);
    modelSelect.addEventListener('change', updateModel);
    tempSlider.addEventListener('input', () => { tempVal.textContent = tempSlider.value; });

    // Theme toggles
    $('#btn-theme').addEventListener('click', toggleTheme);
    $('#btn-theme-topbar').addEventListener('click', toggleTheme);

    // Sidebar
    $('#sidebar-open').addEventListener('click', openSidebar);
    $('#sidebar-close').addEventListener('click', closeSidebar);
    overlay.addEventListener('click', closeSidebar);

    // Suggestions
    $$('.suggestion').forEach(btn => {
        btn.addEventListener('click', () => {
            inputEl.value = btn.dataset.prompt;
            autoResize();
            send();
        });
    });

    updateModel();
}

// ── Chat History Management ────────────────────────────────────────────────

function loadChats() {
    try {
        const stored = localStorage.getItem('nim-chats');
        state.chats = stored ? JSON.parse(stored) : [];
    } catch {
        state.chats = [];
    }
    renderSidebarChats();
}

function saveChats() {
    localStorage.setItem('nim-chats', JSON.stringify(state.chats));
    renderSidebarChats();
}

function renderSidebarChats() {
    recentList.innerHTML = '';

    // Sort by most recent first
    state.chats.sort((a, b) => b.updatedAt - a.updatedAt);

    if (state.chats.length === 0) {
        recentList.innerHTML = '<div class="empty-recent">No recent chats</div>';
        return;
    }

    state.chats.forEach(chat => {
        const item = document.createElement('div');
        item.className = `recent-item ${chat.id === state.currentChatId ? 'active' : ''}`;

        const title = document.createElement('span');
        title.className = 'recent-title';
        title.textContent = chat.title || 'New Chat';

        const delBtn = document.createElement('button');
        delBtn.className = 'btn-del-chat';
        delBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>';
        delBtn.title = "Delete Chat";

        item.addEventListener('click', () => loadChat(chat.id));
        delBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteChat(chat.id);
        });

        item.appendChild(title);
        item.appendChild(delBtn);
        recentList.appendChild(item);
    });
}

function loadChat(id) {
    if (state.streaming) return;
    const chat = state.chats.find(c => c.id === id);
    if (!chat) return;

    state.currentChatId = id;
    state.messages = JSON.parse(JSON.stringify(chat.messages)); // deep copy

    // Clear UI
    messagesEl.querySelectorAll('.msg').forEach(m => m.remove());

    const visible = state.messages.filter(m => m.role !== 'system');
    if (visible.length > 0) {
        welcomeEl.style.display = 'none';
        visible.forEach(m => addMsg(m.role, m.content, false));
        scrollDown();
    } else {
        welcomeEl.style.display = '';
    }

    renderSidebarChats();
    if (window.innerWidth <= 768) closeSidebar();
}

function deleteChat(id) {
    state.chats = state.chats.filter(c => c.id !== id);
    if (state.currentChatId === id) {
        newChat();
    } else {
        saveChats();
    }
}

function newChat() {
    if (state.streaming) return;
    state.currentChatId = null;
    state.messages = [{ role: 'system', content: state.systemPrompt }];

    messagesEl.querySelectorAll('.msg').forEach(m => m.remove());
    welcomeEl.style.display = '';

    renderSidebarChats();
    if (window.innerWidth <= 768) closeSidebar();
}

function updateCurrentChat() {
    if (!state.currentChatId) {
        // Create new chat entry
        state.currentChatId = Date.now().toString();

        const firstUserMsg = state.messages.find(m => m.role === 'user');
        let title = 'New Chat';
        if (firstUserMsg) {
            title = firstUserMsg.content.slice(0, 25) + (firstUserMsg.content.length > 25 ? '...' : '');
        }

        state.chats.push({
            id: state.currentChatId,
            title: title,
            updatedAt: Date.now(),
            messages: JSON.parse(JSON.stringify(state.messages))
        });
    } else {
        // Update existing chat entry
        const chat = state.chats.find(c => c.id === state.currentChatId);
        if (chat) {
            chat.updatedAt = Date.now();
            chat.messages = JSON.parse(JSON.stringify(state.messages));
        }
    }
    saveChats();
}

// ── Theme ──────────────────────────────────────────────────────────────────
function setTheme(t) {
    document.documentElement.setAttribute('data-theme', t);
    localStorage.setItem('nim-theme', t);
    const label = t === 'dark' ? 'Light Mode' : 'Dark Mode';
    const el = $('#theme-label');
    if (el) el.textContent = label;
}
function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    setTheme(current === 'dark' ? 'light' : 'dark');
}

// ── Sidebar ────────────────────────────────────────────────────────────────
function openSidebar() {
    sidebar.classList.add('open');
    overlay.classList.add('active');
}
function closeSidebar() {
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
}

// ── Model ──────────────────────────────────────────────────────────────────
function updateModel() {
    const opt = modelSelect.options[modelSelect.selectedIndex];
    topbarModel.textContent = opt.text.replace(' ⭐', '');
}

// ── Input ──────────────────────────────────────────────────────────────────
function autoResize() {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 180) + 'px';
    btnSend.disabled = !inputEl.value.trim() || state.streaming;
}
function onKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!state.streaming && inputEl.value.trim()) send();
    }
}

// ── Send Message ───────────────────────────────────────────────────────────
async function send() {
    const text = inputEl.value.trim();
    if (!text || state.streaming) return;

    welcomeEl.style.display = 'none';

    // User message
    state.messages.push({ role: 'user', content: text });
    updateCurrentChat();
    addMsg('user', text);

    // Clear input
    inputEl.value = '';
    inputEl.style.height = 'auto';
    btnSend.disabled = true;

    // AI message placeholder
    const aiEl = addMsg('assistant', '', true);
    scrollDown();

    // Streaming state
    state.streaming = true;
    btnSend.classList.add('hidden');
    btnStop.classList.remove('hidden');
    state.abortCtrl = new AbortController();

    let full = '';

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: modelSelect.value,
                messages: state.messages,
                temperature: parseFloat(tempSlider.value),
                max_tokens: 4096,
            }),
            signal: state.abortCtrl.signal,
        });

        if (!res.ok) {
            const errText = await res.text();
            throw new Error(`HTTP ${res.status}: ${errText}`);
        }

        const reader = res.body.getReader();
        const dec = new TextDecoder();
        let buf = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buf += dec.decode(value, { stream: true });
            const lines = buf.split('\n');
            buf = lines.pop() || '';

            for (const line of lines) {
                if (!line.startsWith('data: ')) continue;
                const d = line.slice(6).trim();
                if (d === '[DONE]') continue;
                try {
                    const j = JSON.parse(d);
                    if (!j.choices || !j.choices.length) continue;
                    const delta = j.choices[0].delta;
                    if (delta && delta.content) {
                        full += delta.content;
                        setContent(aiEl, full);
                        scrollDown();
                    }
                } catch (_) { }
            }
        }

        state.messages.push({ role: 'assistant', content: full });
        updateCurrentChat();

    } catch (err) {
        if (err.name === 'AbortError') {
            if (full) {
                state.messages.push({ role: 'assistant', content: full });
                updateCurrentChat();
            }
        } else {
            showErr(aiEl, err.message);
        }
    } finally {
        // Remove typing dots if still there
        const dots = aiEl.querySelector('.typing');
        if (dots) dots.remove();
        state.streaming = false;
        state.abortCtrl = null;
        btnStop.classList.add('hidden');
        btnSend.classList.remove('hidden');
        btnSend.disabled = !inputEl.value.trim();
    }
}

function stop() {
    if (state.abortCtrl) state.abortCtrl.abort();
}

// ── DOM Builders ───────────────────────────────────────────────────────────
function addMsg(role, content, typing = false) {
    const el = document.createElement('div');
    el.className = `msg ${role}`;

    if (role === 'assistant') {
        const av = document.createElement('div');
        av.className = 'msg-avatar';
        av.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>';
        el.appendChild(av);
    }

    const body = document.createElement('div');
    body.className = 'msg-body';

    const txt = document.createElement('div');
    txt.className = 'msg-text';
    if (typing) {
        txt.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
    } else {
        txt.innerHTML = md(content);
    }

    body.appendChild(txt);
    el.appendChild(body);
    messagesEl.appendChild(el);
    return el;
}

function setContent(el, content) {
    const t = el.querySelector('.msg-text');
    t.innerHTML = md(content);
}

function showErr(el, msg) {
    const t = el.querySelector('.msg-text');
    const dots = t.querySelector('.typing');
    if (dots) dots.remove();
    const d = document.createElement('div');
    d.className = 'msg-error';
    d.textContent = '⚠ ' + msg;
    t.appendChild(d);
}

function scrollDown() {
    requestAnimationFrame(() => { messagesEl.scrollTop = messagesEl.scrollHeight; });
}

// ── Markdown Renderer ──────────────────────────────────────────────────────
function md(text) {
    if (!text) return '';
    let h = esc(text);

    // Code blocks
    h = h.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) =>
        `<pre><code class="lang-${lang || 'text'}">${code.trim()}</code></pre>`);

    // Inline code
    h = h.replace(/`([^`\n]+)`/g, '<code>$1</code>');

    // Headers
    h = h.replace(/^#{6}\s+(.+)$/gm, '<h6>$1</h6>');
    h = h.replace(/^#{5}\s+(.+)$/gm, '<h5>$1</h5>');
    h = h.replace(/^#{4}\s+(.+)$/gm, '<h4>$1</h4>');
    h = h.replace(/^#{3}\s+(.+)$/gm, '<h3>$1</h3>');
    h = h.replace(/^#{2}\s+(.+)$/gm, '<h2>$1</h2>');
    h = h.replace(/^#\s+(.+)$/gm, '<h1>$1</h1>');

    // Bold / italic
    h = h.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    h = h.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Blockquote
    h = h.replace(/^&gt;\s+(.+)$/gm, '<blockquote>$1</blockquote>');

    // HR
    h = h.replace(/^---$/gm, '<hr>');

    // Tables
    h = tables(h);

    // Lists
    h = h.replace(/^[\s]*[-*]\s+(.+)$/gm, '<li>$1</li>');
    h = h.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');
    h = h.replace(/^[\s]*\d+\.\s+(.+)$/gm, '<li>$1</li>');

    // Links
    h = h.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

    // Paragraphs
    h = h.replace(/\n\n+/g, '</p><p>');
    h = h.replace(/\n/g, '<br>');
    h = '<p>' + h + '</p>';

    // Cleanup
    const tags = ['h[1-6]', 'pre', 'ul', 'ol', 'blockquote', 'table', 'hr'];
    for (const t of tags) {
        h = h.replace(new RegExp(`<p>\\s*(<${t}[> ])`, 'g'), '$1');
        h = h.replace(new RegExp(`(</${t}>)\\s*</p>`, 'g'), '$1');
    }
    h = h.replace(/<p>\s*<\/p>/g, '');
    h = h.replace(/<p>\s*(<hr>)/g, '$1');
    h = h.replace(/(<hr>)\s*<\/p>/g, '$1');

    return h;
}

function tables(h) {
    const lines = h.split('\n');
    const out = [];
    let i = 0;
    while (i < lines.length) {
        if (i + 1 < lines.length && lines[i].includes('|') && /^\|?[\s\-:|]+\|/.test(lines[i + 1] || '')) {
            let t = '<table><thead><tr>';
            lines[i].split('|').map(c => c.trim()).filter(Boolean).forEach(c => t += `<th>${c}</th>`);
            t += '</tr></thead><tbody>';
            i += 2;
            while (i < lines.length && lines[i].includes('|')) {
                t += '<tr>';
                lines[i].split('|').map(c => c.trim()).filter(Boolean).forEach(c => t += `<td>${c}</td>`);
                t += '</tr>';
                i++;
            }
            t += '</tbody></table>';
            out.push(t);
        } else {
            out.push(lines[i]);
            i++;
        }
    }
    return out.join('\n');
}

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

// ── Start ──────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
