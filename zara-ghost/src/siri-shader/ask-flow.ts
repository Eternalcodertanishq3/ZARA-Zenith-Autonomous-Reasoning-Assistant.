import { Spring } from './spring';
import type { SiriState } from './state';
import type { SiriRenderer } from './renderer';

const PILL_MIN_H = 150;
const ANSWER_PAD_V = 23;
const REVEAL_TICK_MS = 70;

export interface AskFlowDom {
  form: HTMLFormElement | null;
  input: HTMLInputElement | null;
  chips: HTMLElement | null;
  card: HTMLElement | null;
  text: HTMLElement | null;
}

export interface AskFlowOptions {
  siri: SiriState;
  renderer: SiriRenderer | null;
  dom: AskFlowDom;
  onMode?: (mode: string) => void;
}

export function createAskFlow(options: AskFlowOptions) {
  const { siri, renderer, dom, onMode } = options;
  const { form, input, chips, card, text } = dom;

  let mode = 'idle';
  let pending = '';
  let revealTimer = 0;
  let streamEnded = false;
  let angry = false;

  const angerSpring = new Spring(0, { response: 0.45, dampingRatio: 0.9 });

  function feedAnger(dt: number) {
    angerSpring.setTarget(angry && (mode === 'thinking' || mode === 'reply') ? 1 : 0);
    if (renderer) renderer.anger = angerSpring.step(dt);
  }

  function syncChips() {
    if (!chips) return;
    const hasChips = (mode === 'ask' || mode === 'reply') && chipButtons.length > 0;
    chips.classList.toggle('on', hasChips);
    chips.hidden = !hasChips;
  }

  function setMode(next: string) {
    mode = next;
    if (form) form.classList.toggle('on', next === 'ask');
    if (card) card.classList.toggle('on', next === 'reply');
    syncChips();
    if (onMode) onMode(next);
  }

  function appendReveal(part: string) {
    if (!text || !card) return;
    const span = document.createElement('span');
    span.className = 'reveal';
    span.textContent = part;
    text.appendChild(span);
    card.scrollTop = card.scrollHeight;
  }

  function stopReveal() {
    if (revealTimer) {
      window.clearInterval(revealTimer);
      revealTimer = 0;
    }
  }

  function drainTick() {
    if (!pending) {
      if (streamEnded) stopReveal();
      return;
    }
    const segments = pending.length > 240 ? 8 : pending.length > 90 ? 4 : 2;
    let take = '';
    for (let i = 0; i < segments && pending; i += 1) {
      const m = pending.match(/^\s*(?:[^\s]+|\S+)\s*/);
      if (!m) break;
      take += m[0];
      pending = pending.slice(m[0].length);
    }
    if (take) appendReveal(take);
  }

  function startReveal() {
    if (!revealTimer) revealTimer = window.setInterval(drainTick, REVEAL_TICK_MS);
  }

  function cancelStream() {
    stopReveal();
    pending = '';
    streamEnded = false;
    angry = false;
  }

  function openAsk() {
    cancelStream();
    siri.select('answer');
    setMode('ask');
    if (input) {
      input.value = '';
      window.setTimeout(() => input.focus({ preventScroll: true }), 220);
    }
  }

  function close() {
    cancelStream();
    siri.select('idle');
    setMode('idle');
    if (input) input.blur();
  }

  const MAX_CHIPS = 4;
  const chipHoverSprings = Array.from({ length: MAX_CHIPS }, () => new Spring(0, { response: 0.25, dampingRatio: 1 }));
  let chipButtons: HTMLButtonElement[] = [];

  function setChips(labels: string[]) {
    if (!chips) return;
    chips.replaceChildren();
    chipButtons = labels.slice(0, MAX_CHIPS).map((label, i) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'chip';
      button.textContent = label;
      chipHoverSprings[i].jump(0);
      button.addEventListener('pointerenter', () => chipHoverSprings[i].setTarget(1));
      button.addEventListener('pointerleave', () => chipHoverSprings[i].setTarget(0));
      chips.appendChild(button);
      return button;
    });
    syncChips();
  }

  const chipVisSpring = new Spring(0, { response: 0.4, dampingRatio: 1 });
  function feedChipLenses(dt: number) {
    if (!renderer || !chips) return;
    const morphed = (siri.surface.answer || 0) > 0.85;
    const chipsShown = (mode === 'ask' || mode === 'reply') && chipButtons.length > 0 && morphed;
    chipVisSpring.setTarget(chipsShown ? 1 : 0);
    const vis = chipVisSpring.step(dt);
    chips.style.opacity = String(vis);

    if (vis <= 0.001) {
      renderer.chipLenses.states = [0, 0, 0, 0];
      return;
    }

    const rect = renderer.canvas.getBoundingClientRect();
    if (!rect.width || !renderer.width) return;
    const clientPerDevice = rect.width / renderer.width;
    const panelX = rect.left + rect.width * 0.5 + renderer.panelOffset[0] * clientPerDevice;
    const panelY = rect.top + rect.height * 0.5 + renderer.panelOffset[1] * clientPerDevice;

    const hovers = chipHoverSprings.map((spring) => spring.step(dt));
    const states = [0, 0, 0, 0];
    const rects = [
      [0, 0, 0, 0],
      [0, 0, 0, 0],
      [0, 0, 0, 0],
      [0, 0, 0, 0],
    ];

    chipButtons.forEach((chip, i) => {
      if (i >= MAX_CHIPS) return;
      const r = chip.getBoundingClientRect();
      states[i] = vis;
      rects[i] = [
        (r.left + r.width * 0.5 - panelX) / clientPerDevice,
        (r.top + r.height * 0.5 - panelY) / clientPerDevice,
        (r.width * 0.5) / clientPerDevice,
        (r.height * 0.5) / clientPerDevice,
      ];
    });

    renderer.chipLenses.states = states;
    renderer.chipLenses.hovers = hovers;
    renderer.chipLenses.rects = rects;
  }

  const OVERLAY_GAP = 16;
  const pillHeightSpring = new Spring(PILL_MIN_H, { response: 0.45, dampingRatio: 0.9 });
  function feedAnswerHeight(dt: number) {
    if (!renderer || !card) return;
    const canvasCssWidth = renderer.width / Math.max(renderer.dpr, 0.001);
    const squareCap = Math.min(siri.sizes.answer.width, canvasCssWidth - 48);
    const chipsShown = (mode === 'ask' || mode === 'reply') && chipButtons.length > 0;
    const chipBand = chipsShown && chips ? chips.offsetHeight + OVERLAY_GAP : 0;
    const textNatural = mode === 'reply' && text ? text.scrollHeight || card.scrollHeight : 0;
    const content = textNatural + chipBand + ANSWER_PAD_V * 2;
    const target = mode === 'reply' ? Math.min(Math.max(content, PILL_MIN_H), squareCap) : PILL_MIN_H;
    pillHeightSpring.setTarget(target);
    const h = pillHeightSpring.step(dt);
    siri.sizes.answer.height = h;
    card.style.setProperty('--answer-max', `${Math.round(h - ANSWER_PAD_V * 2 - chipBand)}px`);
  }

  let collapsing = false;
  function feedContentOpacity() {
    if (!card || !form) return;
    const a = siri.surface.answer || 0;
    if (mode === 'idle' && a > 0.01) {
      collapsing = true;
      const o = Math.max(0, Math.min(1, (a - 0.55) / 0.45));
      card.style.transition = 'none';
      form.style.transition = 'none';
      card.style.opacity = String(o);
      form.style.opacity = String(o);
    } else if (collapsing) {
      collapsing = false;
      card.style.transition = '';
      form.style.transition = '';
      card.style.opacity = '';
      form.style.opacity = '';
    }
  }

  setMode('idle');

  return {
    get mode() {
      return mode;
    },
    openAsk,
    close,
    setChips,
    startReveal,
    appendReveal,
    tick(dt: number) {
      feedChipLenses(dt);
      feedAnswerHeight(dt);
      feedContentOpacity();
      feedAnger(dt);
    },
    dispose() {
      cancelStream();
    },
  };
}
