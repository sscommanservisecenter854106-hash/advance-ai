// Nexus-AI Client Application
class NexusApp {
  constructor() {
    this.sessionId = null;
    this.ws = null;
    this.isGenerating = false;
    this.currentAssistantMessageEl = null;
    this.currentThoughtEl = null;
    this.currentContentEl = null;
    this.recognition = null;
    this.isListening = false;
    this.ttsEnabled = false;

    this.initElements();
    this.initWebSocket();
    this.initSpeech();
    this.loadSessions();
    this.loadSystemStatus();
    this.bindEvents();
  }

  initElements() {
    this.chatMessages = document.getElementById('chat-messages');
    this.userInput = document.getElementById('user-input');
    this.sendBtn = document.getElementById('send-btn');
    this.newChatBtn = document.getElementById('new-chat-btn');
    this.sessionsList = document.getElementById('sessions-list');
    this.micBtn = document.getElementById('mic-btn');
    this.ttsBtn = document.getElementById('tts-btn');
    this.uploadBtn = document.getElementById('upload-btn');
    this.fileInput = document.getElementById('file-input');

    // Modals
    this.settingsModal = document.getElementById('settings-modal');
    this.settingsBtn = document.getElementById('settings-btn');
    this.closeSettingsBtn = document.getElementById('close-settings-btn');
    this.saveSettingsBtn = document.getElementById('save-settings-btn');

    this.ragModal = document.getElementById('rag-modal');
    this.ragBtn = document.getElementById('rag-btn');
    this.closeRagBtn = document.getElementById('close-rag-btn');
    this.ragSourcesList = document.getElementById('rag-sources-list');
    this.clearRagBtn = document.getElementById('clear-rag-btn');

    // Status Badges
    this.activeModelBadge = document.getElementById('active-model-badge');
    this.ragCountBadge = document.getElementById('rag-count-badge');
    this.toolsCountBadge = document.getElementById('tools-count-badge');
  }

  initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('Connected to Nexus-AI WebSocket server.');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleStreamEvent(data);
    };

    this.ws.onerror = (err) => {
      console.error('WebSocket Error:', err);
    };

    this.ws.onclose = () => {
      console.log('WebSocket connection closed. Retrying in 2 seconds...');
      setTimeout(() => this.initWebSocket(), 2000);
    };
  }

  initSpeech() {
    // Speech Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = false;

      this.recognition.onstart = () => {
        this.isListening = true;
        this.micBtn.classList.add('active');
      };

      this.recognition.onresult = (e) => {
        const transcript = e.results[0][0].transcript;
        this.userInput.value = transcript;
        this.autoGrowInput();
      };

      this.recognition.onend = () => {
        this.isListening = false;
        this.micBtn.classList.remove('active');
      };

      this.recognition.onerror = (e) => {
        console.warn('Speech recognition error:', e.error);
        this.isListening = false;
        this.micBtn.classList.remove('active');
      };
    } else {
      this.micBtn.style.display = 'none';
    }
  }

  toggleSpeechRecognition() {
    if (!this.recognition) return;
    if (this.isListening) {
      this.recognition.stop();
    } else {
      try {
        this.recognition.start();
      } catch (err) {
        console.warn(err);
      }
    }
  }

  speak(text) {
    if (!this.ttsEnabled || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    // Strip markdown formatting for cleaner speech
    const cleanText = text.replace(/[#*`_~\[\]\(\)]/g, ' ').replace(/\s+/g, ' ').trim();
    const utterance = new SpeechSynthesisUtterance(cleanText.slice(0, 400));
    window.speechSynthesis.speak(utterance);
  }

  bindEvents() {
    this.sendBtn.addEventListener('click', () => this.sendMessage());

    this.userInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.sendMessage();
      }
    });

    this.userInput.addEventListener('input', () => this.autoGrowInput());

    this.newChatBtn.addEventListener('click', () => this.startNewSession());

    this.micBtn.addEventListener('click', () => this.toggleSpeechRecognition());

    this.ttsBtn.addEventListener('click', () => {
      this.ttsEnabled = !this.ttsEnabled;
      this.ttsBtn.classList.toggle('active', this.ttsEnabled);
    });

    // File Upload
    this.uploadBtn.addEventListener('click', () => this.fileInput.click());
    this.fileInput.addEventListener('change', (e) => this.handleFileUpload(e));

    // Settings Modal
    this.settingsBtn.addEventListener('click', () => this.openSettings());
    this.closeSettingsBtn.addEventListener('click', () => this.settingsModal.classList.remove('open'));
    this.saveSettingsBtn.addEventListener('click', () => this.saveSettings());

    // RAG Modal
    this.ragBtn.addEventListener('click', () => this.openRagModal());
    this.closeRagBtn.addEventListener('click', () => this.ragModal.classList.remove('open'));
    this.clearRagBtn.addEventListener('click', () => this.clearRagKnowledge());
  }

  autoGrowInput() {
    this.userInput.style.height = 'auto';
    this.userInput.style.height = Math.min(this.userInput.scrollHeight, 160) + 'px';
  }

  async loadSystemStatus() {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      this.activeModelBadge.textContent = data.active_provider.toUpperCase();
      this.toolsCountBadge.textContent = `${data.total_tools} Tools`;
      this.ragCountBadge.textContent = `${data.rag_documents} Docs`;
    } catch (e) {
      console.warn('Failed to load system status', e);
    }
  }

  async loadSessions() {
    try {
      const res = await fetch('/api/sessions');
      const data = await res.json();
      this.sessionsList.innerHTML = '';

      if (data.sessions.length === 0) {
        this.startNewSession();
        return;
      }

      data.sessions.forEach((s) => {
        this.renderSessionItem(s);
      });

      if (!this.sessionId && data.sessions.length > 0) {
        this.switchSession(data.sessions[0].id);
      }
    } catch (e) {
      console.error('Failed to load sessions', e);
    }
  }

  renderSessionItem(session) {
    const item = document.createElement('div');
    item.className = `session-item ${session.id === this.sessionId ? 'active' : ''}`;
    item.dataset.id = session.id;

    const title = document.createElement('span');
    title.className = 'session-title';
    title.textContent = session.title || 'New Conversation';

    const delBtn = document.createElement('button');
    delBtn.className = 'session-delete';
    delBtn.innerHTML = '✕';
    delBtn.title = 'Delete session';
    delBtn.onclick = (e) => {
      e.stopPropagation();
      this.deleteSession(session.id);
    };

    item.appendChild(title);
    item.appendChild(delBtn);

    item.onclick = () => this.switchSession(session.id);
    this.sessionsList.appendChild(item);
  }

  async startNewSession() {
    try {
      const res = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Conversation' })
      });
      const data = await res.json();
      this.sessionId = data.session_id;
      this.chatMessages.innerHTML = '';
      this.showWelcomeHero();
      await this.loadSessions();
    } catch (e) {
      console.error('Failed to create new session', e);
    }
  }

  async switchSession(sessionId) {
    if (this.sessionId === sessionId) return;
    this.sessionId = sessionId;

    // Update active highlight
    document.querySelectorAll('.session-item').forEach((el) => {
      el.classList.toggle('active', el.dataset.id === sessionId);
    });

    try {
      const res = await fetch(`/api/sessions/${sessionId}`);
      const data = await res.json();
      this.chatMessages.innerHTML = '';

      if (data.messages.length === 0) {
        this.showWelcomeHero();
      } else {
        data.messages.forEach((m) => {
          this.renderHistoricalMessage(m);
        });
      }
      this.scrollToBottom();
    } catch (e) {
      console.error('Failed to load session history', e);
    }
  }

  async deleteSession(sessionId) {
    try {
      await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
      if (this.sessionId === sessionId) {
        this.sessionId = null;
      }
      await this.loadSessions();
    } catch (e) {
      console.error('Failed to delete session', e);
    }
  }

  showWelcomeHero() {
    this.chatMessages.innerHTML = `
      <div class="welcome-hero">
        <div class="welcome-logo">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>
        <h1>Nexus-AI Autonomous Platform</h1>
        <p>Your self-contained multimodal AI assistant with live reasoning, Python code execution, web search, calculator, and document knowledge memory.</p>
        <div class="suggestion-grid">
          <div class="suggestion-chip" onclick="app.sendPreset('Compute sqrt(144) + 2**8')">
            <strong>🧮 Fast Math Calculation</strong>
            <span>Compute sqrt(144) + 2**8</span>
          </div>
          <div class="suggestion-chip" onclick="app.sendPreset('Run python code to find the first 15 Fibonacci numbers')">
            <strong>🐍 Python Sandbox</strong>
            <span>Generate first 15 Fibonacci numbers</span>
          </div>
          <div class="suggestion-chip" onclick="app.sendPreset('List the files and directories in the workspace')">
            <strong>📁 Inspect Workspace</strong>
            <span>Show files in project directory</span>
          </div>
          <div class="suggestion-chip" onclick="app.sendPreset('Search web for latest advancements in quantum computing')">
            <strong>🌐 Web Search</strong>
            <span>Look up latest news & tech</span>
          </div>
        </div>
      </div>
    `;
  }

  sendPreset(text) {
    this.userInput.value = text;
    this.sendMessage();
  }

  sendMessage() {
    const text = this.userInput.value.trim();
    if (!text || this.isGenerating) return;

    // Clear welcome hero if present
    const hero = this.chatMessages.querySelector('.welcome-hero');
    if (hero) hero.remove();

    // Render user message
    this.renderUserMessage(text);
    this.userInput.value = '';
    this.userInput.style.height = 'auto';

    // Start assistant message container
    this.createAssistantMessagePlaceholder();

    this.isGenerating = true;
    this.sendBtn.disabled = true;

    // Send via WebSocket
    this.ws.send(JSON.stringify({
      session_id: this.sessionId,
      message: text
    }));
  }

  renderUserMessage(text) {
    const msgEl = document.createElement('div');
    msgEl.className = 'message user';
    msgEl.innerHTML = `
      <div class="message-avatar">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
        </svg>
      </div>
      <div class="message-body">
        <div class="message-author">You</div>
        <div class="message-content">${this.escapeHtml(text)}</div>
      </div>
    `;
    this.chatMessages.appendChild(msgEl);
    this.scrollToBottom();
  }

  createAssistantMessagePlaceholder() {
    const msgEl = document.createElement('div');
    msgEl.className = 'message assistant';
    msgEl.innerHTML = `
      <div class="message-avatar">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2">
          <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 14.5h-2v-2h2zm0-4.5h-2V7h2z"/>
        </svg>
      </div>
      <div class="message-body">
        <div class="message-author">Nexus-AI</div>
        <div class="thought-container"></div>
        <div class="tools-container"></div>
        <div class="message-content"></div>
      </div>
    `;
    this.chatMessages.appendChild(msgEl);
    this.currentAssistantMessageEl = msgEl;
    this.currentContentEl = msgEl.querySelector('.message-content');
    this.currentThoughtEl = null;
    this.currentRawContent = '';
    this.scrollToBottom();
  }

  handleStreamEvent(event) {
    if (!this.currentAssistantMessageEl) return;

    if (event.type === 'session_created') {
      this.sessionId = event.session_id;
      this.loadSessions();
    } else if (event.type === 'thought') {
      this.appendThought(event.data);
    } else if (event.type === 'tool_start') {
      this.appendToolStart(event.name, event.args);
    } else if (event.type === 'tool_end') {
      this.appendToolEnd(event.name, event.result);
    } else if (event.type === 'token') {
      this.currentRawContent += event.data;
      this.currentContentEl.innerHTML = this.renderMarkdown(this.currentRawContent);
      this.scrollToBottom();
    } else if (event.type === 'done') {
      this.isGenerating = false;
      this.sendBtn.disabled = false;
      if (this.ttsEnabled) {
        this.speak(this.currentRawContent);
      }
      this.loadSessions();
      this.loadSystemStatus();
    } else if (event.type === 'error') {
      this.currentContentEl.innerHTML += `<div style="color: var(--accent-rose); margin-top: 8px;">⚠️ ${this.escapeHtml(event.data)}</div>`;
      this.isGenerating = false;
      this.sendBtn.disabled = false;
    }
  }

  appendThought(thoughtText) {
    const container = this.currentAssistantMessageEl.querySelector('.thought-container');
    if (!this.currentThoughtEl) {
      const box = document.createElement('div');
      box.className = 'thought-box';
      box.innerHTML = `
        <div class="thought-header">
          <span>🧠 Reasoning Process</span>
          <span style="font-size: 11px; opacity: 0.8;">Click to toggle</span>
        </div>
        <div class="thought-content">${this.escapeHtml(thoughtText)}</div>
      `;
      const header = box.querySelector('.thought-header');
      const content = box.querySelector('.thought-content');
      header.onclick = () => {
        content.style.display = content.style.display === 'none' ? 'block' : 'none';
      };
      container.appendChild(box);
      this.currentThoughtEl = content;
    } else {
      this.currentThoughtEl.textContent += '\n' + thoughtText;
    }
    this.scrollToBottom();
  }

  appendToolStart(toolName, args) {
    const container = this.currentAssistantMessageEl.querySelector('.tools-container');
    const toolBox = document.createElement('div');
    toolBox.className = 'tool-box';
    toolBox.dataset.tool = toolName;
    toolBox.innerHTML = `
      <div class="tool-header">
        <span>⚡ Executing Tool: <strong>${toolName}</strong></span>
        <span class="tool-status" style="font-size: 11px; opacity: 0.8;">Running...</span>
      </div>
      <div class="tool-result" style="opacity: 0.7;">Input: ${this.escapeHtml(JSON.stringify(args, null, 2))}</div>
    `;
    container.appendChild(toolBox);
    this.scrollToBottom();
  }

  appendToolEnd(toolName, result) {
    const container = this.currentAssistantMessageEl.querySelector('.tools-container');
    const box = container.querySelector(`[data-tool="${toolName}"]:last-child`);
    if (box) {
      const status = box.querySelector('.tool-status');
      if (status) status.textContent = 'Completed';
      const resultEl = box.querySelector('.tool-result');
      if (resultEl) {
        resultEl.style.opacity = '1';
        resultEl.textContent = result;
      }
    }
    this.scrollToBottom();
  }

  renderHistoricalMessage(m) {
    const isUser = m.role === 'user';
    const msgEl = document.createElement('div');
    msgEl.className = `message ${isUser ? 'user' : 'assistant'}`;

    let thoughtsHtml = '';
    if (m.thoughts) {
      thoughtsHtml = `
        <div class="thought-box">
          <div class="thought-header">
            <span>🧠 Reasoning Process</span>
            <span style="font-size: 11px; opacity: 0.8;">Toggle</span>
          </div>
          <div class="thought-content" style="display: none;">${this.escapeHtml(m.thoughts)}</div>
        </div>
      `;
    }

    let toolsHtml = '';
    if (m.tool_calls && m.tool_calls.length > 0) {
      m.tool_calls.forEach((tc) => {
        toolsHtml += `
          <div class="tool-box">
            <div class="tool-header">
              <span>⚡ Tool: <strong>${tc.name}</strong></span>
            </div>
            <div class="tool-result">${this.escapeHtml(tc.result || '')}</div>
          </div>
        `;
      });
    }

    msgEl.innerHTML = `
      <div class="message-avatar">
        ${isUser ? 
          `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>` : 
          `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 14.5h-2v-2h2zm0-4.5h-2V7h2z"/></svg>`}
      </div>
      <div class="message-body">
        <div class="message-author">${isUser ? 'You' : 'Nexus-AI'}</div>
        ${thoughtsHtml}
        ${toolsHtml}
        <div class="message-content">${isUser ? this.escapeHtml(m.content) : this.renderMarkdown(m.content)}</div>
      </div>
    `;

    // Bind thought toggle if present
    const tHeader = msgEl.querySelector('.thought-header');
    if (tHeader) {
      const tContent = msgEl.querySelector('.thought-content');
      tHeader.onclick = () => {
        tContent.style.display = tContent.style.display === 'none' ? 'block' : 'none';
      };
    }

    this.chatMessages.appendChild(msgEl);
  }

  async handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      this.uploadBtn.classList.add('active');
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        alert(`Success: ${data.message} (${data.chunks} chunks created). You can now ask questions about this document!`);
        this.loadSystemStatus();
      } else {
        alert(`Upload failed: ${data.detail || 'Unknown error'}`);
      }
    } catch (err) {
      alert(`Error uploading file: ${err.message}`);
    } finally {
      this.uploadBtn.classList.remove('active');
      this.fileInput.value = '';
    }
  }

  async openSettings() {
    try {
      const res = await fetch('/api/config');
      const data = await res.json();
      const cfg = data.raw;

      document.getElementById('setting-provider').value = cfg.active_provider || 'local';
      document.getElementById('setting-gemini-key').value = cfg.gemini_api_key || '';
      document.getElementById('setting-openai-key').value = cfg.openai_api_key || '';
      document.getElementById('setting-groq-key').value = cfg.groq_api_key || '';
      document.getElementById('setting-ollama-url').value = cfg.ollama_base_url || 'http://localhost:11434';
      document.getElementById('setting-temperature').value = cfg.temperature || 0.7;
      document.getElementById('setting-persona').value = cfg.system_persona || '';

      this.settingsModal.classList.add('open');
    } catch (e) {
      console.error('Failed to open settings', e);
    }
  }

  async saveSettings() {
    const payload = {
      active_provider: document.getElementById('setting-provider').value,
      gemini_api_key: document.getElementById('setting-gemini-key').value,
      openai_api_key: document.getElementById('setting-openai-key').value,
      groq_api_key: document.getElementById('setting-groq-key').value,
      ollama_base_url: document.getElementById('setting-ollama-url').value,
      temperature: parseFloat(document.getElementById('setting-temperature').value) || 0.7,
      system_persona: document.getElementById('setting-persona').value,
      gemini_model: "gemini-2.0-flash",
      openai_model: "gpt-4o-mini",
      groq_model: "llama-3.3-70b-versatile",
      ollama_model: "llama3",
      enabled_tools: ["code_runner", "web_search", "file_manager", "calculator"]
    };

    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        this.settingsModal.classList.remove('open');
        this.loadSystemStatus();
      }
    } catch (e) {
      alert('Error saving configuration: ' + e.message);
    }
  }

  async openRagModal() {
    try {
      const res = await fetch('/api/rag/sources');
      const data = await res.json();
      this.ragSourcesList.innerHTML = '';

      if (data.sources.length === 0) {
        this.ragSourcesList.innerHTML = '<div style="color: var(--text-dim); font-size: 13px;">No documents indexed yet. Use the paperclip button to upload files.</div>';
      } else {
        data.sources.forEach((s) => {
          const row = document.createElement('div');
          row.style.cssText = 'display: flex; justify-content: space-between; padding: 8px 12px; background: var(--bg-card); border-radius: 6px; font-size: 13px;';
          row.innerHTML = `<span>📄 <strong>${this.escapeHtml(s.filename)}</strong></span> <span style="color: var(--text-muted);">${s.chunks} chunks</span>`;
          this.ragSourcesList.appendChild(row);
        });
      }

      this.ragModal.classList.add('open');
    } catch (e) {
      console.error(e);
    }
  }

  async clearRagKnowledge() {
    if (!confirm('Are you sure you want to clear all indexed knowledge documents?')) return;
    try {
      await fetch('/api/rag/clear', { method: 'DELETE' });
      this.openRagModal();
      this.loadSystemStatus();
    } catch (e) {
      alert(e.message);
    }
  }

  scrollToBottom() {
    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
  }

  escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  renderMarkdown(text) {
    if (!text) return '';
    let html = text;

    // Code blocks with syntax copy button
    html = html.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      const safeCode = this.escapeHtml(code.trim());
      return `<pre><code class="language-${lang}">${safeCode}</code></pre>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, (m, c) => `<code>${this.escapeHtml(c)}</code>`);

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Blockquotes
    html = html.replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>');

    // Bold & Italic
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Unordered lists
    html = html.replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // Line breaks
    html = html.replace(/\n\n/g, '<br/><br/>');

    return html;
  }
}

// Global instance
window.app = new NexusApp();
