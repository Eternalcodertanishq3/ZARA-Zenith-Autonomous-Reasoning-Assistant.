import type { SiriSurface, SiriProgress, AudioBands } from './state';

export const WAVE_PRESETS = {
  bloom: {
    audioScale: 1,
    uWhiteClip: 1,
    uUnresolvedScale: 0.14,
    uAmplitude: 0.22,
    uFreq: 1.1,
    uAberrationFreq: 1,
    uWaveSpeed: -1,
    uWaveScale: 0.9,
    uAberration: 2.6,
    uThickness: 3,
    uIntensity: 2,
    uFalloff: 1.7,
    uEdgeMask: 0.4,
    uEdgeMaskInset: 0,
    uBandFill: 30000,
    uBandFillThickness: 0.08,
    uSoftness: 2.5,
    uLowAmplitude: 6,
    uLowIntensity: 1.5,
    uMidAberration: 0.8,
    uMidAberrationAmplitude: 0.05,
    uMidBandFill: 0,
    uMidSoftness: 0.4,
    uHighAberration: 0.5,
    uHighAberrationAmplitude: 0.06,
  },
};

export type WavePreset = typeof WAVE_PRESETS.bloom;

export interface UniformEntry {
  name: string;
  type?: string;
  value: number | number[];
}

export function waveUniforms(surface: SiriSurface, bands: AudioBands, preset: WavePreset = WAVE_PRESETS.bloom): UniformEntry[] {
  const { audioScale, ...uniformValues } = preset;
  return [
    { name: 'uResolved', value: surface.sharedResolved },
    { name: 'uLayerOpacity', value: surface.waveLayerOpacity },
    { name: 'uEffectScale', value: surface.effectScale },
    { name: 'uAnchor', type: 'vec2', value: [0.5, 0.5] },
    { name: 'uWavePhase', value: surface.wavePhase },
    { name: 'uLow', value: bands.low * audioScale },
    { name: 'uMid', value: bands.mid * audioScale },
    { name: 'uHigh', value: bands.high * audioScale },
    ...Object.entries(uniformValues).map(([name, value]) => ({ name, value: value as number })),
  ];
}

export function dotsUniforms(surface: SiriSurface, progress: SiriProgress[]): UniformEntry[] {
  return [
    { name: 'uDotsResolved', value: surface.dotsResolved },
    { name: 'uEffectScale', value: surface.effectScale },
    { name: 'uAnchor', type: 'vec2', value: [0.5, 0.5] },
    { name: 'uRotation', value: 0.7 },
    { name: 'uRingRadius', value: 0.45 },
    { name: 'uDotRadius', value: 0.1 },
    { name: 'uPairOffset', value: 0.085 },
    { name: 'uPairSmoothness', value: 0.2 },
    { name: 'uSmoothness', value: 0.2 },
    { name: 'uProgress0', value: progress[0].value },
    { name: 'uProgress1', value: progress[1].value },
    { name: 'uProgress2', value: progress[2].value },
    { name: 'uProgress3', value: progress[3].value },
    { name: 'uProgress4', value: progress[4].value },
    { name: 'uProgress5', value: progress[5].value },
    { name: 'uScaleDuration', value: 2 },
    { name: 'uScaleStagger', value: 0.167 },
    { name: 'uScaleMin', value: 0.001 },
    { name: 'uScaleMax', value: 0.65 },
    { name: 'uGlowIntensity', value: 0.04 },
    { name: 'uFalloffPower', value: 0.7 },
    { name: 'uGlowFadeStart', value: 0 },
    { name: 'uGlowFadeEnd', value: 0.7 },
    { name: 'uDotsAberration', value: -0.05 },
    { name: 'uCenterCore', value: 0.5 },
    { name: 'uDotsScale', value: 1 },
    { name: 'uAppear', value: surface.dotsAppear },
    { name: 'uGather', value: surface.gather },
    { name: 'uCharge', value: surface.charge },
    { name: 'uFlash', value: surface.flash },
  ];
}
