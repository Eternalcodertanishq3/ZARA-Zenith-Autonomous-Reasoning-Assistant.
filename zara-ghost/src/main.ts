import './styles.css';
import { SiriRenderer } from './siri-shader/renderer';
import { createSiriState } from './siri-shader/state';
import { AudioAnalyzer } from './siri-shader/audio-analyzer';
import { createAskFlow } from './siri-shader/ask-flow';
import { initChatMode } from './modes/chat';
import { initSystemMode } from './modes/system';

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
  chat:    { width: 480, height: 160 },
  code:    { width: 720, height: 380 },
  system:  { width: 480, height: 280 },
  vision:  { width: 560, height: 220 },
};

const MODE_CHIPS = ['💬 Chat', '⚡ Code', '◉ System', '👁 Vision'];

// ═══════════════════════════════════════════════════════════════
//  Global state & modules
// ═══════════════════════════════════════════════════════════════

let currentTaskMode = 'chat';
const canvas = document.getElementById('siri-canvas') as HTMLCanvasElement;
const pillOverlay = document.getElementById('pill-overlay') as HTMLDivElement;

const renderer = new SiriRenderer(canvas, 'bloom', true);
const siriState = createSiriState();
const audio = new AudioAnalyzer();

let animationFrameId: number | null = null;
let lastTimestamp = 0;

const flow = createAskFlow({
  siri: siriState,
  renderer,
  dom: {
    form: document.getElementById('ask-form') as HTMLFormElement,
    input: document.getElementById('ask-input') as HTMLInputElement,
    chips: document.getElementById('ask-chips'),
    card: document.getElementById('answer-card'),
    text: document.getElementById('answer-text'),
  },
});

const chatMode = initChatMode(
  {
    input: document.getElementById('ask-input') as HTMLInputElement,
    messages: document.getElementById('answer-text'),
  },
  siriState
);

const systemMode = initSystemMode();

// Initialize 4 mode chips inside glass pill
flow.setChips(MODE_CHIPS);

// Attach explicit click listeners to all mode buttons
function attachChipClickListeners(): void {
  const chipButtons = document.querySelectorAll('.chip, .ask-chips button');
  chipButtons.forEach((btn, index) => {
    const modes = ['chat', 'code', 'system', 'vision'];
    const mode = btn.getAttribute('data-mode') || modes[index] || 'chat';
    
    btn.addEventListener('pointerdown', (e) => e.stopPropagation());
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      e.preventDefault();
      switchTaskMode(mode);
    });
  });
}

attachChipClickListeners();

function switchTaskMode(task: string): void {
  currentTaskMode = task;
  const size = TASK_SIZES[task] || TASK_SIZES.chat;
  siriState.sizes.answer = { width: size.width, height: size.height };
  flow.openAsk();

  pillOverlay.classList.add('expanded');
  pillOverlay.style.width = `${size.width - 24}px`;
  pillOverlay.style.height = `${size.height - 24}px`;

  tauriInvoke('morph_window', { task });

  // Update active chip button
  const buttons = document.querySelectorAll('.ask-chips button');
  buttons.forEach((b) => {
    if (b.getAttribute('data-mode') === task || b.textContent?.toLowerCase().includes(task)) {
      b.classList.add('active');
    } else {
      b.classList.remove('active');
    }
  });

  // Toggle active class on layout panels
  const askForm = document.getElementById('ask-form');
  const answerCard = document.getElementById('answer-card');
  const codeLayout = document.getElementById('layout-code');
  const sysLayout = document.getElementById('layout-system');
  const visLayout = document.getElementById('layout-vision');

  if (askForm) askForm.classList.toggle('on', task === 'chat');
  if (answerCard) answerCard.classList.toggle('on', task === 'chat');
  if (codeLayout) codeLayout.classList.toggle('on', task === 'code');
  if (sysLayout) sysLayout.classList.toggle('on', task === 'system');
  if (visLayout) visLayout.classList.toggle('on', task === 'vision');

  if (task === 'system') {
    systemMode.startMonitoring(({ cpu, ram, gpu }) => {
      const cpuVal = document.getElementById('cpu-val');
      const ramVal = document.getElementById('ram-val');
      const gpuVal = document.getElementById('gpu-val');
      if (cpuVal) cpuVal.textContent = `${cpu}%`;
      if (ramVal) ramVal.textContent = `${ram}%`;
      if (gpuVal) gpuVal.textContent = `${gpu}%`;
      const cpuFill = document.getElementById('cpu-fill');
      const ramFill = document.getElementById('ram-fill');
      const gpuFill = document.getElementById('gpu-fill');
      if (cpuFill) cpuFill.style.width = `${cpu}%`;
      if (ramFill) ramFill.style.width = `${ram}%`;
      if (gpuFill) gpuFill.style.width = `${gpu}%`;
    });
  } else {
    systemMode.stopMonitoring();
  }
}

// ═══════════════════════════════════════════════════════════════
//  Window Blur & Focus
// ═══════════════════════════════════════════════════════════════

window.addEventListener('blur', () => {
  if (flow.mode !== 'idle') {
    flow.close();
    tauriInvoke('morph_window', { task: 'idle' });
  }
});

pillOverlay.addEventListener('pointerdown', (e: PointerEvent) => {
  const target = e.target as HTMLElement;
  if (!target.closest('input') && !target.closest('button')) {
    tauriInvoke('start_drag');
  }
});

// ═══════════════════════════════════════════════════════════════
//  Hit testing & Glass interaction
// ═══════════════════════════════════════════════════════════════

function hitGlass(clientX: number, clientY: number): boolean {
  const ballX = window.innerWidth * 0.5;
  const ballY = window.innerHeight * 0.5;
  const morph = Math.max(0, Math.min(1, siriState.surface.answer));
  const pad = 26 * (1 - morph);
  const base = siriState.sizes.expanded.width;
  const pillW = Math.min(siriState.sizes.answer.width, window.innerWidth - 48);
  const halfW = (base + (pillW - base) * morph) * 0.5 + pad;
  const halfH = (base + (siriState.sizes.answer.height - base) * morph) * 0.5 + pad;
  return Math.abs(clientX - ballX) <= halfW && Math.abs(clientY - ballY) <= halfH;
}

let dragging = false;
let pressedInside = false;
let moved = false;
let grabPointer = [0, 0];
let longPressTimer = 0;
let voiceHold = false;

function startVoiceHold(): void {
  longPressTimer = 0;
  if (!dragging || moved || flow.mode !== 'idle') return;
  voiceHold = true;
  siriState.select('listening');
  audio.start().catch(() => {});
}

function endVoiceHold(): void {
  if (!voiceHold) return;
  voiceHold = false;
  audio.stop();
  siriState.select('idle');
}

canvas.addEventListener('pointerdown', (e: PointerEvent) => {
  // Check if click target is a button, input, or inside pillOverlay
  const hitTarget = document.elementFromPoint(e.clientX, e.clientY) as HTMLElement;
  if (hitTarget && (hitTarget.closest('.chip') || hitTarget.closest('#pill-overlay') || hitTarget.tagName === 'BUTTON' || hitTarget.tagName === 'INPUT')) {
    return; // Allow HTML click event to fire on the button!
  }

  moved = false;
  pressedInside = hitGlass(e.clientX, e.clientY);
  grabPointer = [e.clientX, e.clientY];
  if (pressedInside) {
    dragging = true;
    siriState.setPressed(true);
    if (flow.mode === 'idle') {
      longPressTimer = window.setTimeout(startVoiceHold, 450);
    }
  }
});

canvas.addEventListener('pointermove', (e: PointerEvent) => {
  if (!dragging) return;
  const dx = e.clientX - grabPointer[0];
  const dy = e.clientY - grabPointer[1];
  if (!moved && Math.hypot(dx, dy) > 6) {
    moved = true;
    window.clearTimeout(longPressTimer);
    longPressTimer = 0;
  }
  if (moved) {
    tauriInvoke('start_drag');
  }
});

function onRelease(e: PointerEvent): void {
  const wasDragging = dragging;
  dragging = false;
  siriState.setPressed(false);
  window.clearTimeout(longPressTimer);
  longPressTimer = 0;
  const wasVoice = voiceHold;
  endVoiceHold();

  if (!e || e.type !== 'pointerup') return;
  if (wasVoice) return;
  if (wasDragging && moved) return;

  if (pressedInside) {
    if (flow.mode === 'idle' || flow.mode === 'reply') {
      switchTaskMode('chat');
    } else if (flow.mode === 'thinking') {
      flow.close();
      tauriInvoke('morph_window', { task: 'idle' });
    }
  } else if (flow.mode !== 'idle') {
    flow.close();
    tauriInvoke('morph_window', { task: 'idle' });
  }
}

canvas.addEventListener('pointerup', onRelease);
canvas.addEventListener('pointercancel', onRelease);
canvas.addEventListener('lostpointercapture', onRelease);

// ═══════════════════════════════════════════════════════════════
//  Chat Backend
// ═══════════════════════════════════════════════════════════════

async function sendMessage(): Promise<void> {
  await chatMode.send();
}

(window as any).sendMessage = sendMessage;
(window as any).getCurrentTaskMode = () => currentTaskMode;

// ═══════════════════════════════════════════════════════════════
//  Render Loop
// ═══════════════════════════════════════════════════════════════

function animate(timestamp: number): void {
  animationFrameId = requestAnimationFrame(animate);
  const dt = Math.min(0.1, (timestamp - (lastTimestamp || timestamp)) / 1000);
  lastTimestamp = timestamp;

  const currentBands = audio.update(dt);
  flow.tick(dt);
  siriState.tick(dt, currentBands);

  renderer.render({
    surface: siriState.surface,
    progress: siriState.progress,
    bands: currentBands,
    sizes: siriState.sizes,
    dt,
  });
}

animationFrameId = requestAnimationFrame(animate);

window.addEventListener('beforeunload', () => {
  if (animationFrameId) cancelAnimationFrame(animationFrameId);
  flow.dispose();
  audio.stop();
  systemMode.stopMonitoring();
  renderer.dispose();
});
