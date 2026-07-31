import './styles.css';
import { SiriRenderer } from './siri-shader/renderer';
import { createSiriState } from './siri-shader/state';
import type { AudioBands } from './siri-shader/state';

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
//  Task-specific pill sizes
// ═══════════════════════════════════════════════════════════════

const TASK_SIZES: Record<string, { width: number; height: number }> = {
  chat:    { width: 480, height: 220 },
  code:    { width: 820, height: 460 },
  system:  { width: 440, height: 340 },
  vision:  { width: 600, height: 160 },
};

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
const taskLabel = document.getElementById('task-label') as HTMLSpanElement;

// ═══════════════════════════════════════════════════════════════
//  Renderer setup
// ═══════════════════════════════════════════════════════════════

try {
  renderer = new SiriRenderer(canvas, 'bloom');
} catch (e) {
  console.error('WebGL2 init failed:', e);
}

siriState.select('idle');

// ═══════════════════════════════════════════════════════════════
//  morphTo — state transitions
// ═══════════════════════════════════════════════════════════════

function morphTo(task: string): void {
  if (task === currentTask && task !== 'idle') return;
  currentTask = task;

  if (task === 'idle') {
    siriState.select('idle');
    pillOverlay.classList.remove('expanded');
  } else if (task === 'thinking') {
    siriState.select('thinking');
    pillOverlay.classList.remove('expanded');
  } else {
    const size = TASK_SIZES[task] || TASK_SIZES.chat;
    siriState.sizes.answer = { width: size.width, height: size.height };
    siriState.select('answer');
    pillOverlay.classList.add('expanded');
    pillOverlay.style.width = `${size.width - 24}px`;
    pillOverlay.style.height = `${size.height - 24}px`;
  }

  tauriInvoke('morph_window', { task });
  updateLayout(task);
}

function updateLayout(task: string): void {
  const isExpanded = task !== 'idle' && task !== 'thinking';

  taskLabel.textContent = task === 'idle' ? 'ZARA' : task.toUpperCase();

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
}

// ═══════════════════════════════════════════════════════════════
//  Click outside pill → close to orb
// ═══════════════════════════════════════════════════════════════

canvas.addEventListener('click', (e: MouseEvent) => {
  if (currentTask === 'idle') return;

  // Check if click is outside the glass panel region
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const x = (e.clientX - rect.left) * dpr;
  const y = (e.clientY - rect.top) * dpr;
  const cx = canvas.width * 0.5;
  const cy = canvas.height * 0.5;
  const size = TASK_SIZES[currentTask] || TASK_SIZES.chat;
  const halfW = size.width * dpr * 0.5;
  const halfH = size.height * dpr * 0.5;

  if (Math.abs(x - cx) > halfW || Math.abs(y - cy) > halfH) {
    morphTo('idle');
  }
});

// ═══════════════════════════════════════════════════════════════
//  Press & drag interaction with strict orb hit-testing
// ═══════════════════════════════════════════════════════════════

function getOrbHit(e: MouseEvent): { dist: number; isInside: boolean } {
  const rect = canvas.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const clickY = e.clientY - rect.top;
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;
  const dx = clickX - centerX;
  const dy = clickY - centerY;
  const dist = Math.hypot(dx, dy);
  const hitRadius = currentTask === 'idle' ? 68 : 100;
  return { dist, isInside: dist <= hitRadius };
}

let isPressed = false;
let pressStartTime = 0;
let pressTimeout: ReturnType<typeof setTimeout> | null = null;

canvas.addEventListener('pointerdown', (e: PointerEvent) => {
  const { isInside } = getOrbHit(e);

  if (currentTask === 'idle') {
    if (!isInside) return;
  } else {
    // In expanded pill mode, check if click is outside interactive elements/pill bounds
    const target = e.target as HTMLElement;
    const isInteractive = target.closest('.chat-input') || target.closest('.tab') || target.closest('.win-btn') || target.closest('.file-item');

    const rect = canvas.getBoundingClientRect();
    const dx = e.clientX - rect.left - rect.width / 2;
    const dy = e.clientY - rect.top - rect.height / 2;
    const size = TASK_SIZES[currentTask] || TASK_SIZES.chat;

    if (!isInteractive && (Math.abs(dx) > size.width / 2 || Math.abs(dy) > size.height / 2)) {
      morphTo('idle');
      return;
    }
  }

  isPressed = true;
  pressStartTime = performance.now();
  siriState.setPressed(true);
  try {
    canvas.setPointerCapture(e.pointerId);
  } catch {}
  canvas.style.cursor = 'grabbing';

  if (currentTask === 'idle') {
    pressTimeout = setTimeout(() => {
      if (isPressed) {
        siriState.select('listening');
      }
    }, 500);
  }
});

canvas.addEventListener('pointerup', (e: PointerEvent) => {
  const pressDuration = performance.now() - pressStartTime;
  const { isInside } = getOrbHit(e);

  isPressed = false;
  siriState.setPressed(false);
  try {
    canvas.releasePointerCapture(e.pointerId);
  } catch {}

  canvas.style.cursor = isInside && currentTask === 'idle' ? 'grab' : 'default';

  if (pressTimeout) {
    clearTimeout(pressTimeout);
    pressTimeout = null;
  }

  if (siriState.state === 'listening') {
    siriState.select('idle');
    return;
  }

  if (pressDuration < 350 && currentTask === 'idle' && isInside) {
    morphTo('chat');
  }
});

canvas.addEventListener('pointermove', (e: PointerEvent) => {
  const { isInside } = getOrbHit(e);

  if (currentTask === 'idle') {
    canvas.style.cursor = isInside ? (isPressed ? 'grabbing' : 'grab') : 'default';
  } else {
    canvas.style.cursor = 'default';
  }

  if (isPressed && currentTask === 'idle') {
    tauriInvoke('start_drag');
  }
});

// ═══════════════════════════════════════════════════════════════
//  Chat backend
// ═══════════════════════════════════════════════════════════════

async function sendMessage(): Promise<void> {
  const input = document.getElementById('chat-input') as HTMLInputElement;
  const text = input.value.trim();
  if (!text) return;
  input.value = '';

  addChatMessage(text, 'user');
  siriState.select('thinking');

  try {
    const response = await fetch('http://127.0.0.1:11434/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'gemma3:4b', prompt: text, stream: false }),
    });

    if (response.ok) {
      const data = await response.json();
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
//  System monitor
// ═══════════════════════════════════════════════════════════════

function updateSystemStats(): void {
  if (currentTask !== 'system') return;
  const cpu = Math.round(15 + Math.random() * 30);
  const ram = Math.round(40 + Math.random() * 20);
  const gpu = Math.round(10 + Math.random() * 25);

  const cpuVal = document.getElementById('cpu-val');
  const ramVal = document.getElementById('ram-val');
  const gpuVal = document.getElementById('gpu-val');
  if (cpuVal) cpuVal.textContent = `${cpu}%`;
  if (ramVal) ramVal.textContent = `${ram}%`;
  if (gpuVal) gpuVal.textContent = `${gpu}%`;

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

  siriState.tick(dt, bands);

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

animationFrameId = requestAnimationFrame(animate);

// ═══════════════════════════════════════════════════════════════
//  Expose globals
// ═══════════════════════════════════════════════════════════════

(window as any).morphTo = morphTo;
(window as any).sendMessage = sendMessage;

window.addEventListener('beforeunload', () => {
  if (animationFrameId) cancelAnimationFrame(animationFrameId);
  renderer?.dispose();
});
