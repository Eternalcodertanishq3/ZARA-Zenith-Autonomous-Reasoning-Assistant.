import { Spring, SpringOptions } from './spring';

const EXPANDED_WIDTH = 128;

const WAVE_IN_SPRING: SpringOptions = { response: 0.314, dampingRatio: 1 };
const WAVE_OUT_SPRING: SpringOptions = { response: 0.3, dampingRatio: 1 };
const PRESS_SPRING: SpringOptions = { response: 0.28, dampingRatio: 1 };
const DOTS_APPEAR_SPRING: SpringOptions = { response: 0.314, dampingRatio: 1 };
const PROGRESS_SPRING: SpringOptions = { duration: 0.9, bounce: 0.55 };

const PROGRESS_STAGGER_S = 0.2;
const FLIP_INTERVAL_S = 2.5;

const CONCLUDE_GATHER_S = 0.6;
const CONCLUDE_CHARGE_S = 0.3;
const GATHER_IN_SPRING: SpringOptions = { response: 0.5, dampingRatio: 1 };
const GATHER_BURST_SPRING: SpringOptions = { duration: 0.55, bounce: 0.5 };
const CHARGE_SPRING: SpringOptions = { response: 0.18, dampingRatio: 1 };
const FLASH_DECAY = 7;
const SIM_MAX_STEP_S = 1 / 30;
const WAVE_PHASE_WRAP = 62.831848;
const WAVE_SPEED_BASE = -2.5;
const WAVE_SPEED_AUDIO = -12;
const AUDIO_DRIVE_SCALE = 0.4;

const ANSWER_SPRING: SpringOptions = { response: 0.5, dampingRatio: 0.8 };

export interface SiriSurface {
  waveOpacity: number;
  wavePhase: number;
  waveResolved: number;
  sharedResolved: number;
  dotsAppear: number;
  dotsResolved: number;
  effectScale: number;
  waveLayerOpacity: number;
  press: number;
  gather: number;
  charge: number;
  flash: number;
  answer: number;
}

export interface AudioBands {
  low: number;
  mid: number;
  high: number;
}

export interface SiriProgress {
  value: number;
}

export interface SiriSizes {
  expanded: { width: number };
  answer: { width: number; height: number };
}

interface StatePreset {
  waveActive: boolean;
  fluidDotsActive: boolean;
}

const STATE_PRESETS: Record<string, StatePreset> = {
  idle: { waveActive: true, fluidDotsActive: false },
  listening: { waveActive: true, fluidDotsActive: false },
  thinking: { waveActive: false, fluidDotsActive: true },
  answer: { waveActive: false, fluidDotsActive: false },
};

function zeroVelocity() {
  return { fluidDots: 0, effectScale: 0 };
}

function targetsFor(preset: StatePreset) {
  return {
    fluidDots: preset.fluidDotsActive ? 1 : -1,
    effectScale: preset.fluidDotsActive ? 2 / 3 : 1,
  };
}

function integrateFluidSim(sim: { current: Record<string, number>; velocity: Record<string, number>; target: Record<string, number> }, dt: number) {
  let remaining = Math.min(Math.max(dt, 0), 0.1);
  while (remaining > 0) {
    const step = Math.min(remaining, SIM_MAX_STEP_S);
    for (const key of ['fluidDots', 'effectScale']) {
      const accel = (sim.current[key] - sim.target[key]) * -400 + sim.velocity[key] * -40;
      sim.velocity[key] += accel * step;
      sim.current[key] += sim.velocity[key] * step;
    }
    remaining -= step;
  }
}

function applySimToSurface(surface: SiriSurface, current: Record<string, number>) {
  surface.dotsResolved = current.fluidDots;
  surface.effectScale = current.effectScale;
  surface.waveResolved = surface.waveOpacity * 2 - 1;
  surface.sharedResolved = Math.max(surface.waveResolved, surface.dotsResolved, 0);
  surface.waveLayerOpacity = 0.98 * Math.min(1, Math.max(0, surface.waveOpacity));
}

function audioDrive(bands: AudioBands | null): number {
  if (!bands) return 0;
  return Math.max(0, Math.min(1, Math.max(bands.low || 0, bands.mid || 0, bands.high || 0) * AUDIO_DRIVE_SCALE));
}

function advanceWavePhase(surface: SiriSurface, dt: number, bands: AudioBands | null) {
  const speed = WAVE_SPEED_BASE + WAVE_SPEED_AUDIO * audioDrive(bands);
  surface.wavePhase = (surface.wavePhase + speed * dt) % WAVE_PHASE_WRAP;
  if (surface.wavePhase < 0) surface.wavePhase += WAVE_PHASE_WRAP;
}

export interface SiriState {
  sizes: SiriSizes;
  surface: SiriSurface;
  progress: SiriProgress[];
  readonly state: string;
  select(name: string): void;
  conclude(): number;
  setPressed(pressed: boolean): void;
  tick(dt: number, bands: AudioBands | null): void;
}

export function createSiriState(): SiriState {
  const initialTargets = targetsFor(STATE_PRESETS.idle);

  const surface: SiriSurface = {
    waveOpacity: 0,
    wavePhase: 0,
    waveResolved: -1,
    sharedResolved: 0,
    dotsAppear: 0,
    dotsResolved: initialTargets.fluidDots,
    effectScale: initialTargets.effectScale,
    waveLayerOpacity: 0,
    press: 0,
    gather: 0,
    charge: 0,
    flash: 0,
    answer: 0,
  };

  const springs = {
    waveOpacity: new Spring(surface.waveOpacity, WAVE_IN_SPRING),
    dotsAppear: new Spring(surface.dotsAppear, DOTS_APPEAR_SPRING),
    press: new Spring(surface.press, PRESS_SPRING),
  };

  const sim = {
    current: { ...initialTargets },
    velocity: zeroVelocity(),
    target: { ...initialTargets },
  };

  const progress: SiriProgress[] = Array.from({ length: 6 }, () => ({ value: 0 }));
  const progressSprings = progress.map(() => new Spring(0, PROGRESS_SPRING));

  let state = 'idle';
  let flipTarget = 0;
  let prevFlipTarget = 0;
  let thinkTimer = 0;
  let timeSinceFlip = Number.POSITIVE_INFINITY;

  const gatherSpring = new Spring(0, GATHER_IN_SPRING);
  const chargeSpring = new Spring(0, CHARGE_SPRING);
  const answerSpring = new Spring(0, ANSWER_SPRING);
  let concludePhase: string | null = null;
  let concludeTimer = 0;
  let flashValue = 0;

  function flip() {
    prevFlipTarget = flipTarget;
    flipTarget = flipTarget > 0.5 ? 0 : 1;
    timeSinceFlip = 0;
  }

  function resetFlip() {
    prevFlipTarget = 0;
    flipTarget = 0;
    thinkTimer = 0;
    timeSinceFlip = Number.POSITIVE_INFINITY;
    for (const spring of progressSprings) spring.setTarget(0, PROGRESS_SPRING);
  }

  function resetConclude() {
    concludePhase = null;
    concludeTimer = 0;
    flashValue = 0;
    gatherSpring.jump(0);
    gatherSpring.setOptions(GATHER_IN_SPRING);
    chargeSpring.jump(0);
  }

  return {
    sizes: { expanded: { width: EXPANDED_WIDTH }, answer: { width: 460, height: 150 } },
    surface,
    progress,
    get state() { return state; },

    select(name: string) {
      const preset = STATE_PRESETS[name];
      if (!preset) return;
      const targets = targetsFor(preset);
      const targetsChanged = sim.target.fluidDots !== targets.fluidDots || sim.target.effectScale !== targets.effectScale;
      state = name;
      thinkTimer = 0;
      springs.waveOpacity.setTarget(preset.waveActive ? 1 : 0, preset.waveActive ? WAVE_IN_SPRING : WAVE_OUT_SPRING);
      sim.target = targets;
      if (targetsChanged) sim.velocity = zeroVelocity();
      if (name !== 'thinking') resetFlip();
      if (name === 'listening' || name === 'thinking') resetConclude();
      answerSpring.setTarget(name === 'answer' ? 1 : 0, ANSWER_SPRING);
    },

    conclude(): number {
      if (state !== 'thinking' || concludePhase) return 0;
      concludePhase = 'gather';
      concludeTimer = 0;
      thinkTimer = 0;
      gatherSpring.setTarget(1, GATHER_IN_SPRING);
      return Math.round((CONCLUDE_GATHER_S + CONCLUDE_CHARGE_S) * 1000);
    },

    setPressed(pressed: boolean) {
      springs.press.setTarget(pressed ? 1 : 0, PRESS_SPRING);
    },

    tick(dt: number, bands: AudioBands | null) {
      surface.waveOpacity = springs.waveOpacity.step(dt);
      surface.press = springs.press.step(dt);
      integrateFluidSim(sim, dt);
      applySimToSurface(surface, sim.current);
      advanceWavePhase(surface, dt, bands);

      springs.dotsAppear.setTarget(Math.max(surface.dotsResolved, 0), DOTS_APPEAR_SPRING);
      surface.dotsAppear = springs.dotsAppear.step(dt);

      if (concludePhase) {
        concludeTimer += dt;
        if (concludePhase === 'gather' && concludeTimer >= CONCLUDE_GATHER_S) {
          concludePhase = 'charge';
          chargeSpring.setTarget(1, CHARGE_SPRING);
        } else if (concludePhase === 'charge' && concludeTimer >= CONCLUDE_GATHER_S + CONCLUDE_CHARGE_S) {
          concludePhase = null;
          flashValue = 1;
          gatherSpring.setTarget(0, GATHER_BURST_SPRING);
          chargeSpring.jump(0);
        }
      }
      surface.gather = gatherSpring.step(dt);
      surface.charge = chargeSpring.step(dt);
      surface.answer = answerSpring.step(dt);
      flashValue *= Math.exp(-FLASH_DECAY * dt);
      if (flashValue < 0.001) flashValue = 0;
      surface.flash = flashValue;

      if (state === 'thinking' && surface.dotsResolved > 0) {
        if (!concludePhase) thinkTimer += dt;
        if (thinkTimer >= FLIP_INTERVAL_S) {
          thinkTimer = 0;
          flip();
        }
      } else {
        resetFlip();
      }

      timeSinceFlip += dt;
      for (let i = 0; i < progressSprings.length; i += 1) {
        const target = i * PROGRESS_STAGGER_S > timeSinceFlip ? prevFlipTarget : flipTarget;
        progressSprings[i].setTarget(target, PROGRESS_SPRING);
        progress[i].value = progressSprings[i].step(dt);
      }
    },
  };
}
