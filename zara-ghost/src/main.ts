import './styles.css';
import { SiriRenderer } from './siri-shader/renderer';
import { createSiriState } from './siri-shader/state';
import type { AudioBands } from './siri-shader/state';

// ═══════════════════════════════════════════════════════════════
//  Tauri integration
// ═══════════════════════════════════════════════════════════════

declare global {
  interface Window {
    __TAURI__?: {
      core: {
        invoke: (cmd: string, args?: Record<string, unknown>) => Promise<unknown>;
      };
    };
  }
}

function tauriInvoke(cmd: string, args?: Record<string, unknown>): void {
  window.__TAURI__?.core?.invoke(cmd, args).catch(() => {});
}

// ═══════════════════════════════════════════════════════════════
//  Global state
// ═══════════════════════════════════════════════════════════════

let currentTask = 'idle';
let renderer: SiriRenderer | null = null;
const siriState = createSiriState();
const bands: AudioBands = { low: 0, mid: 0, high: 0 };
let animationFrameId: number | null = null;
let lastTimestamp = 0;

// ═══════════════════════════════════════════════════════════════
//  DOM references
// ═══════════════════════════════════════════════════════════════

const canvas = document.getElementById('siri-canvas') as HTMLCanvasElement;
const pillOverlay = document.getElementById('pill-overlay') as HTMLDivElement;
const siriHint = document.getElementById('siri-hint') as HTMLDivElement;
const winHeader = document.getElementById('win-header') as HTMLDivElement;
const winContent = document.getElementById('win-content') as HTMLDivElement;
const cornerTabs = document.getElementById('corner-tabs') as HTMLDivElement;
const taskLabel = document.getElementById('task-label') as HTMLSpanElement;

// ═══════════════════════════════════════════════════════════════
//  Renderer setup
// ═══════════════════════════════════════════════════════════════

try {
  renderer = new SiriRenderer(canvas, 'bloom');
} catch (e) {
  console.error('WebGL2 init failed:', e);
}

// Start in idle → wave active
siriState.select('idle');

// ═══════════════════════════════════════════════════════════════
//  morphTo — state transitions connected to backend
// ═══════════════════════════════════════════════════════════════

function morphTo(task: string): void {
  if (task === currentTask && task !== 'idle') return;
  currentTask = task;

  // Map ZARA tasks to shader states
  if (task === 'idle') {
    siriState.select('idle');
  } else if (task === 'thinking') {
    siriState.select('thinking');
  } else {
    // chat, code, system, vision → answer state (pill morph)
    siriState.select('answer');
  }

  // Update Tauri window
  tauriInvoke('morph_window', { task });

  // Update DOM visibility
  updateLayout(task);
}

function updateLayout(task: string): void {
  const isIdle = task === 'idle';
  const isThinking = task === 'thinking';
  const isExpanded = !isIdle && !isThinking;

  // Hide/show overlay elements
  siriHint.style.opacity = isIdle ? '1' : '0';
  siriHint.style.pointerEvents = isIdle ? 'auto' : 'none';

  winHeader.style.display = isExpanded ? 'flex' : 'none';
  winContent.style.opacity = isExpanded ? '1' : '0';
  cornerTabs.style.display = isExpanded ? 'flex' : 'none';

  if (isExpanded) {
    // Delay opacity for glass morph to complete
    setTimeout(() => {
      winHeader.style.opacity = '1';
      cornerTabs.style.opacity = '1';
    }, 250);
  }

  // Update task label
  taskLabel.textContent = task.toUpperCase();

  // Show correct layout panel
  const layouts = document.querySelectorAll('.layout');
  layouts.forEach((l) => {
    (l as HTMLElement).style.display = 'none';
  });

  if (isExpanded) {
    const layoutId = `layout-${task}`;
    const activeLayout = document.getElementById(layoutId);
    if (activeLayout) {
      activeLayout.style.display = 'flex';
    }
  }

  // Configure pill overlay size for expanded states
  if (isExpanded) {
    pillOverlay.style.width = `${siriState.sizes.answer.width}px`;
    pillOverlay.style.height = `${siriState.sizes.answer.height}px`;
  } else {
    pillOverlay.style.width = '';
    pillOverlay.style.height = '';
  }
}

// ═══════════════════════════════════════════════════════════════
//  Mouse / drag interaction
// ═══════════════════════════════════════════════════════════════

let isPressed = false;
let pressStartTime = 0;

canvas.addEventListener('pointerdown', (e: PointerEvent) => {
  isPressed = true;
  pressStartTime = performance.now();
  siriState.setPressed(true);
  canvas.setPointerCapture(e.pointerId);
});

canvas.addEventListener('pointerup', (e: PointerEvent) => {
  const pressDuration = performance.now() - pressStartTime;
  isPressed = false;
  siriState.setPressed(false);
  canvas.releasePointerCapture(e.pointerId);

  // Short click → toggle between idle and answer/chat
  if (pressDuration < 300 && currentTask === 'idle') {
    morphTo('chat');
  } else if (pressDuration < 300 && currentTask !== 'idle') {
    // Already expanded, do nothing on click (tabs handle navigation)
  }
});

canvas.addEventListener('pointermove', (_e: PointerEvent) => {
  if (!isPressed) return;
  // Drag → use Tauri native drag
  if (isPressed && currentTask === 'idle') {
    tauriInvoke('start_drag');
  }
});

// Double click → back to idle
canvas.addEventListener('dblclick', () => {
  if (currentTask !== 'idle') {
    morphTo('idle');
  }
});

// ═══════════════════════════════════════════════════════════════
//  Chat functionality (connected to backend)
// ═══════════════════════════════════════════════════════════════

async function sendMessage(): Promise<void> {
  const input = document.getElementById('chat-input') as HTMLInputElement;
  const text = input.value.trim();
  if (!text) return;
  input.value = '';

  // Add user message
  addChatMessage(text, 'user');

  // Switch to thinking state
  siriState.select('thinking');

  try {
    const response = await fetch('http://127.0.0.1:11434/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'gemma3:4b',
        prompt: text,
        stream: false,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      // Conclude thinking → burst flash → back to answer
      const burstDelay = siriState.conclude();
      setTimeout(() => {
        siriState.select('answer');
        addChatMessage(data.response || 'No response.', 'bot');
      }, burstDelay);
    } else {
      siriState.select('answer');
      addChatMessage('Error: Could not reach model.', 'bot');
    }
  } catch {
    siriState.select('answer');
    addChatMessage('Error: Backend not available.', 'bot');
  }
}

function addChatMessage(text: string, sender: 'user' | 'bot'): void {
  const messagesEl = document.getElementById('chat-messages');
  if (!messagesEl) return;
  const div = document.createElement('div');
  div.className = `msg ${sender}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// ═══════════════════════════════════════════════════════════════
//  System monitor (connected to backend)
// ═══════════════════════════════════════════════════════════════

function updateSystemStats(): void {
  if (currentTask !== 'system') return;

  // Simulated system stats (replace with real Tauri system info commands)
  const cpu = Math.round(15 + Math.random() * 30);
  const ram = Math.round(40 + Math.random() * 20);
  const gpu = Math.round(10 + Math.random() * 25);

  const cpuVal = document.getElementById('cpu-val');
  const ramVal = document.getElementById('ram-val');
  const gpuVal = document.getElementById('gpu-val');

  if (cpuVal) cpuVal.textContent = `${cpu}%`;
  if (ramVal) ramVal.textContent = `${ram}%`;
  if (gpuVal) gpuVal.textContent = `${gpu}%`;

  // Update progress bars
  const fills = document.querySelectorAll('.sys-fill');
  if (fills[0]) (fills[0] as HTMLElement).style.width = `${cpu}%`;
  if (fills[1]) (fills[1] as HTMLElement).style.width = `${ram}%`;
  if (fills[2]) (fills[2] as HTMLElement).style.width = `${gpu}%`;
}

setInterval(updateSystemStats, 2000);

// ═══════════════════════════════════════════════════════════════
//  Render loop
// ═══════════════════════════════════════════════════════════════

function animate(timestamp: number): void {
  animationFrameId = requestAnimationFrame(animate);
  const dt = Math.min(0.1, (timestamp - (lastTimestamp || timestamp)) / 1000);
  lastTimestamp = timestamp;

  // Advance state machine
  siriState.tick(dt, bands);

  // Render
  if (renderer && !renderer.error) {
    renderer.render({
      surface: siriState.surface,
      progress: siriState.progress,
      bands,
      sizes: siriState.sizes,
      dt,
    });
  }
}

// Start animation
animationFrameId = requestAnimationFrame(animate);

// ═══════════════════════════════════════════════════════════════
//  Expose globals for HTML onclick handlers
// ═══════════════════════════════════════════════════════════════

(window as any).morphTo = morphTo;
(window as any).sendMessage = sendMessage;
(window as any).minimize = () => morphTo('idle');
(window as any).closeWindow = () => {
  tauriInvoke('morph_window', { task: 'idle' });
  morphTo('idle');
};

// Cleanup on unload
window.addEventListener('beforeunload', () => {
  if (animationFrameId) cancelAnimationFrame(animationFrameId);
  renderer?.dispose();
});
