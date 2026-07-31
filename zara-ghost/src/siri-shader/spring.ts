const TAU = Math.PI * 2;
const MASS = 1;
const MIN_RESPONSE = 1e-4;

interface ResponseOptions {
  response: number;
  dampingRatio: number;
}

interface DurationOptions {
  duration: number;
  bounce: number;
}

interface RawOptions {
  mass?: number;
  stiffness: number;
  damping: number;
}

export type SpringOptions = ResponseOptions | DurationOptions | RawOptions;

interface SpringParams {
  mass: number;
  stiffness: number;
  damping: number;
  naturalAngularFrequency: number;
}

function paramsFromResponse(opts: ResponseOptions): SpringParams {
  const safeResponse = Math.max(opts.response, MIN_RESPONSE);
  const ratio = Math.max(0, opts.dampingRatio);
  const omega = TAU / safeResponse;
  const stiffness = MASS * omega * omega;
  const damping = 2 * ratio * MASS * omega;
  return { mass: MASS, stiffness, damping, naturalAngularFrequency: omega };
}

function paramsFromDuration(opts: DurationOptions): SpringParams {
  return paramsFromResponse({
    response: opts.duration,
    dampingRatio: Math.max(0.05, 1 - Math.max(0, opts.bounce)),
  });
}

function normalizeOptions(options: SpringOptions): SpringParams {
  if ('stiffness' in options && 'damping' in options) {
    const mass = (options as RawOptions).mass || MASS;
    const omega = Math.sqrt(options.stiffness / mass);
    return { mass, stiffness: options.stiffness, damping: options.damping, naturalAngularFrequency: omega };
  }
  if ('duration' in options && 'bounce' in options) return paramsFromDuration(options as DurationOptions);
  return paramsFromResponse(options as ResponseOptions);
}

function stepSpring(value: number, velocity: number, target: number, params: SpringParams, dt: number): [number, number] {
  const omegaSq = params.stiffness / params.mass;
  const omega = params.naturalAngularFrequency;
  const decay = params.damping / (2 * params.mass);
  const t = Math.max(dt, 0);
  const x0 = value - target;

  if (t <= 0 || (x0 === 0 && velocity === 0)) return [value, velocity];

  let x: number;
  let v: number;
  if (decay < omega) {
    const wd = Math.sqrt(omegaSq - decay * decay);
    const envelope = Math.exp(-decay * t);
    const cos = Math.cos(wd * t);
    const sin = Math.sin(wd * t);
    const a = x0;
    const b = (velocity + decay * x0) / wd;
    const disp = a * cos + b * sin;
    x = envelope * disp;
    v = envelope * (-decay * disp + (-a * wd * sin + b * wd * cos));
  } else if (omega < decay) {
    const wd = Math.sqrt(decay * decay - omegaSq);
    const r1 = -decay + wd;
    const r2 = -decay - wd;
    const a = (velocity - r2 * x0) / (r1 - r2);
    const b = x0 - a;
    const e1 = Math.exp(r1 * t);
    const e2 = Math.exp(r2 * t);
    x = a * e1 + b * e2;
    v = a * r1 * e1 + b * r2 * e2;
  } else {
    const envelope = Math.exp(-decay * t);
    const c = velocity + decay * x0;
    const disp = x0 + c * t;
    x = envelope * disp;
    v = envelope * (c - decay * disp);
  }
  return [target + x, v];
}

export class Spring {
  value: number;
  velocity: number;
  target: number;
  private parameters: SpringParams;

  constructor(value: number, options: SpringOptions) {
    this.value = value;
    this.velocity = 0;
    this.target = value;
    this.parameters = normalizeOptions(options);
  }

  setOptions(options: SpringOptions): void {
    this.parameters = normalizeOptions(options);
  }

  setTarget(target: number, options?: SpringOptions): void {
    if (options) this.setOptions(options);
    this.target = target;
  }

  jump(value: number): void {
    this.value = value;
    this.velocity = 0;
    this.target = value;
  }

  step(dt: number): number {
    [this.value, this.velocity] = stepSpring(this.value, this.velocity, this.target, this.parameters, dt);
    return this.value;
  }
}
