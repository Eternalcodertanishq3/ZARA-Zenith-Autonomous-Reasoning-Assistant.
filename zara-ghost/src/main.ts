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

function drawOrbitRings(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  r: number,
  time: number,
  isBack: boolean
) {
  const numRings = 3;
  const colors = [
    'rgba(56, 189, 248, 0.85)', // Cyan
    'rgba(192, 132, 252, 0.75)', // Purple
    'rgba(244, 63, 94, 0.75)',  // Rose Red
  ];

  for (let i = 0; i < numRings; i++) {
    const rx = r * 1.32;
    const ry = r * 0.38 + Math.sin(time * 1.2 + i) * 5;
    const rot = -0.35 + i * 0.35;
    const baseColor = colors[i % colors.length];

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(rot);

    // Split 3D orbit into back arc and front arc
    const startAngle = isBack ? Math.PI : 0;
    const endAngle = isBack ? Math.PI * 2 : Math.PI;

    // Draw multi-strand wave ribbon bundle (matching Siri Reference Image 2)
    const strands = 4;
    for (let s = 0; s < strands; s++) {
      const strandOffsetY = (s - (strands - 1) / 2) * 2.8;
      ctx.beginPath();
      ctx.ellipse(0, strandOffsetY, rx, ry + s * 0.8, 0, startAngle, endAngle);
      ctx.lineWidth = s === 1 || s === 2 ? 1.8 : 1.0;
      ctx.strokeStyle = baseColor;
      ctx.shadowBlur = 8;
      ctx.shadowColor = baseColor;
      ctx.stroke();
    }

    ctx.restore();
  }
}

function initSiriCanvas() {
  const canvas = document.getElementById('siri-canvas') as HTMLCanvasElement;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  canvas.width = 300;
  canvas.height = 300;

  let time = 0;

  function render() {
    if (!ctx) return;
    time += 0.025;
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const r = 92;

    ctx.clearRect(0, 0, w, h);

    // 1. Draw 3D Orbiting Back Rings (behind sphere)
    drawOrbitRings(ctx, cx, cy, r, time, true);

    // 2. Clip Outer Glass Sphere
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.clip();

    // Dark Obsidian Sphere Base
    const bgGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
    bgGrad.addColorStop(0, '#0c0f24');
    bgGrad.addColorStop(0.65, '#060814');
    bgGrad.addColorStop(1, '#020309');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, w, h);

    ctx.globalCompositeOperation = 'screen';

    // Blob 1: Vibrant Siri Cyan (Image 2)
    const cX = cx + Math.sin(time * 1.1) * 26;
    const cY = cy + Math.cos(time * 0.95) * 24 - 12;
    const cyanGrad = ctx.createRadialGradient(cX, cY, 4, cX, cY, r * 0.82);
    cyanGrad.addColorStop(0, 'rgba(34, 211, 238, 0.98)');
    cyanGrad.addColorStop(0.45, 'rgba(6, 182, 212, 0.65)');
    cyanGrad.addColorStop(1, 'rgba(6, 182, 212, 0)');
    ctx.fillStyle = cyanGrad;
    ctx.beginPath();
    ctx.arc(cX, cY, r * 0.82, 0, Math.PI * 2);
    ctx.fill();

    // Blob 2: Deep Crimson / Rose Red (Image 2)
    const mX = cx + Math.cos(time * 0.85) * 24;
    const mY = cy + Math.sin(time * 1.25) * 26 + 18;
    const magGrad = ctx.createRadialGradient(mX, mY, 4, mX, mY, r * 0.88);
    magGrad.addColorStop(0, 'rgba(225, 29, 72, 0.98)');
    magGrad.addColorStop(0.5, 'rgba(244, 63, 94, 0.7)');
    magGrad.addColorStop(1, 'rgba(225, 29, 72, 0)');
    ctx.fillStyle = magGrad;
    ctx.beginPath();
    ctx.arc(mX, mY, r * 0.88, 0, Math.PI * 2);
    ctx.fill();

    // Blob 3: Vivid Purple / Violet (Image 2)
    const vX = cx + Math.sin(time * 1.35 + 1.8) * 28;
    const vY = cy + Math.cos(time * 1.15 + 1.8) * 24 - 8;
    const vioGrad = ctx.createRadialGradient(vX, vY, 4, vX, vY, r * 0.78);
    vioGrad.addColorStop(0, 'rgba(168, 85, 247, 0.95)');
    vioGrad.addColorStop(0.5, 'rgba(192, 132, 252, 0.6)');
    vioGrad.addColorStop(1, 'rgba(168, 85, 247, 0)');
    ctx.fillStyle = vioGrad;
    ctx.beginPath();
    ctx.arc(vX, vY, r * 0.78, 0, Math.PI * 2);
    ctx.fill();

    // Blob 4: White Hot Core Flare (Center)
    const coreX = cx + Math.sin(time * 1.6) * 10;
    const coreY = cy + Math.cos(time * 1.6) * 10;
    const coreGrad = ctx.createRadialGradient(coreX, coreY, 0, coreX, coreY, r * 0.5);
    coreGrad.addColorStop(0, 'rgba(255, 255, 255, 1)');
    coreGrad.addColorStop(0.35, 'rgba(255, 235, 255, 0.85)');
    coreGrad.addColorStop(1, 'rgba(255, 255, 255, 0)');
    ctx.fillStyle = coreGrad;
    ctx.beginPath();
    ctx.arc(coreX, coreY, r * 0.45, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();

    // 3. 3D Glass Shell Glint (NO white stroke line border)
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);

    const glassGrad = ctx.createLinearGradient(cx - r, cy - r, cx + r, cy + r);
    glassGrad.addColorStop(0, 'rgba(255, 255, 255, 0.45)');
    glassGrad.addColorStop(0.2, 'rgba(255, 255, 255, 0.1)');
    glassGrad.addColorStop(0.5, 'transparent');
    ctx.fillStyle = glassGrad;
    ctx.fill();
    ctx.restore();

    // 4. Draw 3D Orbiting Front Rings (wrapping around front of sphere, Image 1)
    drawOrbitRings(ctx, cx, cy, r, time, false);

    requestAnimationFrame(render);
  }

  render();
}

// Initial position & state sync
morphTo('idle');
initSiriCanvas();

// System stats polling mockup
setInterval(() => {
  if (currentTask === 'system') {
    const cpuEl = document.getElementById('cpu-val');
    const ramEl = document.getElementById('ram-val');
    if (cpuEl) cpuEl.textContent = Math.floor(Math.random() * 40 + 15) + '%';
    if (ramEl) ramEl.textContent = (Math.random() * 4 + 6).toFixed(1) + 'GB';
  }
}, 2000);
