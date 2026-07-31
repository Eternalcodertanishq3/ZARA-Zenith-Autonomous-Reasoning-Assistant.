import { invoke } from '@tauri-apps/api/core';

const container = document.getElementById('zara-container') as HTMLElement;
const idleCore = document.getElementById('idle-core') as HTMLElement;
const header = document.getElementById('win-header') as HTMLElement;
const content = document.getElementById('win-content') as HTMLElement;
const tabs = document.getElementById('corner-tabs') as HTMLElement;
const dragHandle = document.getElementById('drag-handle') as HTMLElement;
const taskLabel = document.getElementById('task-label') as HTMLElement;

const layouts: Record<string, { w: number; h: number; radius: string }> = {
  idle:   { w: 120, h: 120, radius: '50%' },
  chat:   { w: 420, h: 680, radius: '18px' },
  code:   { w: 900, h: 520, radius: '16px' },
  system: { w: 380, h: 380, radius: '22px' },
  vision: { w: 700, h: 140, radius: '16px' },
};

let ws: WebSocket | null = null;
let currentTask = 'idle';

// Single clean WebSocket connection
function connectWS() {
  const wsUrl = 'ws://localhost:8000/ws/brain';
  
  ws = new WebSocket(wsUrl);
  ws.onopen = () => console.log(`Connected to ZARA nervous system at ${wsUrl}`);
  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.type === 'response' && data.text) {
        addMessage(data.text, 'bot');
      }
      if (data.type === 'task_detected' && data.task) {
        morphTo(data.task);
      }
      if (data.type === 'system_stats') {
        const cpuEl = document.getElementById('cpu-val');
        const ramEl = document.getElementById('ram-val');
        if (cpuEl && data.cpu) cpuEl.textContent = data.cpu;
        if (ramEl && data.ram) ramEl.textContent = data.ram;
      }
      if (data.type === 'vision_update' && data.content) {
        const visEl = document.getElementById('vision-text');
        if (visEl) visEl.textContent = data.content;
      }
    } catch (err) {
      console.warn('Received non-JSON message:', e.data);
      if (typeof e.data === 'string' && e.data.trim()) {
        addMessage(e.data, 'bot');
      }
    }
  };
  ws.onerror = (err) => console.error('WebSocket error:', err);
  ws.onclose = () => setTimeout(connectWS, 3000);
}
connectWS();

function morphTo(task: string) {
  currentTask = task;
  const L = layouts[task] || layouts.chat;
  
  container.setAttribute('data-task', task);
  container.style.width = `${L.w}px`;
  container.style.height = `${L.h}px`;
  container.style.borderRadius = L.radius;
  
  // Call Rust to sync native window position & size
  try {
    invoke('morph_window', { task });
  } catch (e) {
    console.log('Tauri invoke morph_window:', e);
  }
  
  if (task === 'idle') {
    container.style.background = 'transparent';
    container.style.backdropFilter = 'none';
    container.style.border = 'none';
    container.style.boxShadow = 'none';
    idleCore.style.display = 'flex';
    header.style.display = 'none';
    header.style.opacity = '0';
    content.style.opacity = '0';
    tabs.style.display = 'none';
    tabs.style.opacity = '0';
    dragHandle.style.display = 'none';
    setTimeout(() => {
      document.querySelectorAll('.layout').forEach(l => (l as HTMLElement).style.display = 'none');
    }, 300);
  } else {
    container.style.background = '';
    container.style.backdropFilter = '';
    container.style.border = '';
    container.style.boxShadow = '';
    idleCore.style.display = 'none';
    header.style.display = 'flex';
    tabs.style.display = 'flex';
    dragHandle.style.display = 'block';
    setTimeout(() => {
      header.style.opacity = '1';
      content.style.opacity = '1';
      tabs.style.opacity = '1';
    }, 80);
    
    document.querySelectorAll('.layout').forEach(l => (l as HTMLElement).style.display = 'none');
    const active = document.getElementById(`layout-${task}`);
    if (active) {
      active.style.display = task === 'chat' || task === 'vision' ? 'flex' : 'block';
      if (task === 'code') active.style.display = 'flex';
    }
    taskLabel.textContent = task.toUpperCase();
  }
}

function addMessage(text: string, sender: 'bot' | 'user') {
  const div = document.createElement('div');
  div.className = `msg ${sender}`;
  div.textContent = text;
  const msgs = document.getElementById('chat-messages')!;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function sendMessage() {
  const input = document.getElementById('chat-input') as HTMLInputElement;
  const text = input.value.trim();
  if (!text) return;
  addMessage(text, 'user');
  input.value = '';
  
  // Auto detect task locally if offline fallback
  const detected = detectTask(text);
  if (detected !== 'chat') morphTo(detected);

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'text', content: text }));
  }
}

function startDrag() {
  try {
    invoke('start_drag');
  } catch (e) {
    console.log('Tauri drag fallback', e);
  }
}

function minimize() {
  morphTo('idle');
}

function closeWindow() {
  if (ws) ws.close();
  window.close();
}

function detectTask(text: string): string {
  const t = text.toLowerCase();
  if (t.includes('write a function') || t.includes('python script') || t.includes('code for me')) return 'code';
  if (t.includes('cpu usage') || t.includes('ram usage') || t.includes('system stats')) return 'system';
  if (t.includes('what do you see') || t.includes('look at my screen') || t.includes('camera on')) return 'vision';
  return 'chat';
}

// Attach orb click listener
idleCore.addEventListener('click', () => morphTo('chat'));

// Expose to window for inline onclick handlers
(window as any).morphTo = morphTo;
(window as any).sendMessage = sendMessage;
(window as any).startDrag = startDrag;
(window as any).minimize = minimize;
(window as any).closeWindow = closeWindow;

// System stats polling mockup
setInterval(() => {
  if (currentTask === 'system') {
    const cpuEl = document.getElementById('cpu-val');
    const ramEl = document.getElementById('ram-val');
    if (cpuEl) cpuEl.textContent = Math.floor(Math.random() * 40 + 15) + '%';
    if (ramEl) ramEl.textContent = (Math.random() * 4 + 6).toFixed(1) + 'GB';
  }
}, 2000);
