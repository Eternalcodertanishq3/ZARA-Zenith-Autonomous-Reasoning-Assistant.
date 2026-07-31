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
//  Task-specific pill sizes (Matching z1han exact proportions)
// ═══════════════════════════════════════════════════════════════

const TASK_SIZES: Record<string, { width: number; height: number }> = {
  chat:    { width: 480, height: 160 },
  code:    { width: 780, height: 420 },
  system:  { width: 480, height: 320 },
  vision:  { width: 600, height: 200 },
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
//  morphTo — state transitions with spring animation
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
  taskLabel.textContent = task === 'idle' ? 'ZARA' : 'Ask ZARA';

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

  // Update active chip state
  const chips = document.querySelectorAll('.chip');
  chips.forEach((c) => c.classList.remove('active'));
  const targetClass = task === 'vision' ? 'chip-eye' : `chip-${task}`;
  const activeChip = document.querySelector(`.${targetClass}`);
  if (activeChip) activeChip.classList.add('active');
}

// ═══════════════════════════════════════════════════════════════
//  Click Outside Handling & Focus Blur
// ═══════════════════════════════════════════════════════════════

// 1. Loss of window focus -> Clicking anywhere outside ZARA's window on screen morphs back to orb!
window.addEventListener('blur', () => {
  if (currentTask !== 'idle') {
    morphTo('idle');
  }
});

// 2. Click on canvas background outside #pill-overlay -> morph back to orb!
window.addEventListener('pointerdown', (e: PointerEvent) => {
  if (currentTask === 'idle') return;

  const target = e.target as HTMLElement;
  // If click is inside the pill container, keep pill open!
  if (target.closest('#pill-overlay')) {
    return;
  }

  // Clicked outside #pill-overlay -> morph back to orb!
  morphTo('idle');
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
  const hitRadius = currentTask === 'idle' ? 60 : 120;
  return { dist, isInside: dist <= hitRadius };
}

let isPressed = false;
let pressStartTime = 0;
let pressTimeout: ReturnType<typeof setTimeout> | null = null;

canvas.addEventListener('pointerdown', (e: PointerEvent) => {
  const { isInside } = getOrbHit(e);

  if (currentTask === 'idle') {
    if (!isInside) return;
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

  canvas.style.cursor = 'default';

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

canvas.addEventListener('pointermove', (_e: PointerEvent) => {
  canvas.style.cursor = isPressed ? 'grabbing' : 'default';

  if (isPressed) {
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
